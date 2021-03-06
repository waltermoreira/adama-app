import typing

from functools import partial
import json
import sys
from textwrap import dedent
import time

import pika


class AbstractQueueConnection(object):
    """A task queue.

    Implement this interface to provide a task queue for the
    workers.

    """

    CONNECTION_TIMEOUT = 10  # second

    def connect(self):
        """Establish the connection.

        This method should be able to retry the connection until
        CONNECTION_TIMEOUT or sleep and try at the end of the
        CONNECTION_TIMEOUT period.  Lack of network connection is NOT an
        error until the CONNECTION_TIMEOUT period expires.
        """
        pass

    def send(self, message):
        """Send an asynchronous message."""
        pass

    def receive(self):
        """Return multiple responses.

        It should be a generator that produces each response.  The
        user is supposed to send `True` back to the generator when all
        the responses are returned.

        """
        pass

    def consume_forever(self, callback):
        """Consume and invoke `callback`.

        `callback` has the signature::

            f(message, responder)

        where `responder` is a function with signature::

            g(message)

        that can be used to answer to the producer.

        This method should be able to retry the connection.

        """
        pass

    def delete(self):
        """Delete this queue."""
        pass


class QueueConnection(AbstractQueueConnection):

    def __init__(self, queue_host, queue_port, queue_name):
        self.queue_host = queue_host
        self.queue_port = queue_port
        self.queue_name = queue_name
        self.connect()

    def delete(self):
        self.channel.queue_delete(self.queue_name)

    def connect(self):
        """Establish a connection with the task queue."""

        start_t = time.time()
        while True:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.queue_host,
                                              port=self.queue_port))
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                return
            except pika.exceptions.AMQPConnectionError:
                if time.time() - start_t > self.CONNECTION_TIMEOUT:
                    raise
                time.sleep(0.5)

    def send(self, message):
        """Send a message to the queue.

        Return immediately. Use `receive` to get the result.

        """
        self.response = None
        self.result = self.channel.queue_declare(exclusive=True)
        self.result_queue = self.result.method.queue
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue_name,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       # make message persistent
                                       delivery_mode=2,
                                       reply_to=self.result_queue))

    def receive(self):
        """Receive results from the queue.

        A generator returning objects from the queue. It will block if
        there are no objects yet.

        The end of the stream is marked by sending `True` back to the
        generator.

        """
        while True:
            (ok, props, message) = self.channel.basic_get(
                self.result_queue, no_ack=True)
            if ok is not None:
                is_done = yield message
                if is_done:
                    return

    def consume_forever(self, callback, **kwargs):
        while True:
            try:
                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(partial(self.on_consume, callback),
                                           queue=self.queue_name,
                                           no_ack=True,
                                           **kwargs)
                self.channel.start_consuming()
            except pika.exceptions.ChannelClosed:
                if kwargs.get('exclusive', False):
                    # if the channel closes and the connection is
                    # 'exclusive', just return. This is so temporary
                    # connections can be clean up automatically.
                    return
            except Exception as exc:
                # on exceptions, try to reconnect to the queue
                # it will give up after CONNECTION_TIMEOUT
                pass
            self.connect()

    def on_consume(self, callback, ch, method, props, body):

        def responder(result):
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             body=result)

        callback(body, responder)


class Producer(QueueConnection):
    """Send messages to the queue exchange and receive answers.

    The `receive` method behaves as a generator, returning a stream of
    messages.

    """

    def send(self, message):
        """Send a dictionary as message."""

        super(Producer, self).send(json.dumps(message))

    def receive(self):
        """Receive messages until getting `END`."""

        g = super(Producer, self).receive()
        for message in g:
            if message == 'END':
                # save the object after 'END' as metadata, so the
                # client can use it
                self.metadata = json.loads(next(g))
                g.send(True)
                return
            yield json.loads(message)


def check_queue(display=False):
    """Check that we can establish a connection to the queue."""

    from adama.config import Config

    host = Config.get('queue', 'host')
    port = Config.getint('queue', 'port')
    try:
        q = QueueConnection(queue_host=host,
                            queue_port=port,
                            queue_name='test')
        q.delete()
        return True
    except Exception:
        if display:
            print(dedent(
                """
                Cannot connect to queue exchange at {0}:{1}
                with dummy queue "test".
                Please, check ~/.adama.conf
                """.format(host, port)), file=sys.stderr)
        return False
