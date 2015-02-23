#!/usr/bin/env python3

import adama.routes

if __name__ == '__main__':
    adama.routes.app.run(debug=True, host='0.0.0.0', port=8080)
