"""ServerDensity plugin for monitoring all services under a dotcloud account.

Copyright 2012 Rajeesh Nair.

Some parts of this script are derived from the `dotcloud` client tool, 
originally written and copyrighted by dotCloud Inc. For the same reason, 
this script is being distributed under the same set of conditions put 
forward by dotCloud Inc for the above-mentioned tool.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

__author__ = "Rajeesh Nair"
__version__ = "0.1"

import json
import hmac
import hashlib
import datetime
import urllib
import re
import os
import httplib

class Config(dict):

    """Copied from dotcloud.cli.config"""

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, dict):
            return self.__class__(value)
        return value

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]

    def __repr__(self):
        return '<Config ' + dict.__repr__(self) + '>'

def load_config(config_file):
    """Load data from json file to a Config instance."""
    config = json.load(file(config_file))
    if config is None:
        config = {}
    return Config(config)

class DotcloudInfo(object):

    """The ServerDensity Plugin class for monitoring Dotcloud services."""

    dotcloud_version = "0.4.3"
    dotcloud_config_path = os.path.join(
        os.path.expanduser('~/.dotcloud'), 'dotcloud.conf'
    )
    dotcloud_env_path = os.path.join(
        os.path.expanduser('~'), 'environment.json'
    )

    def __init__(self, config, logger, raw_config):
        """config & raw_config are stored but never used! logger required."""
        self.config = config
        self.logger = logger
        self.raw_config = raw_config
        self._request = None 

    def load_user_config(self):
        """Load data from dotcloud.conf to a Config instance."""
        if not os.path.exists(self.dotcloud_config_path):
            self.logger.error(
                'Error: %s does not exist.', self.dotcloud_config_path
            )
            return None 
        config = load_config(self.dotcloud_config_path)
        if 'url' not in config or 'apikey' not in config:
            self.logger.error(
                'Configuration file not valid. Please copy it over here.'
            )
            return None
        return config
 
    def sign_request(self, method, request):
        """Sign an Https request with the given api_key."""
        cfg = self.load_user_config()
        if cfg is None:
            return {}
        (access_key, secret_key) = cfg.apikey.split(':')
        date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') 
        sign = hmac.new(
            bytes(secret_key), 
            ':'.join((method, request, date)), 
            hashlib.sha1
        ).hexdigest()
        headers = {
            'X-DotCloud-Access-Key': access_key,
            'X-DotCloud-Auth-Version': '1.0',
            'X-DotCloud-Date': date,
            'X-DotCloud-Authorization': sign
        }
        return headers

    def get_service_info(self, service):
        """Get the result of info command as a dict."""
        project = self.get_project_name()
        cmd = ['info', '{0}.{1}'.format(project, service)]
        if self._request:
            req = self._request
        else:
            req = httplib.HTTPSConnection('api.dotcloud.com', 443)
            self._request = req
        cmd = urllib.quote(json.dumps(cmd))
        query = '/run?q=%s' % cmd
        headers = self.sign_request('GET', query)
        version = self.dotcloud_version
        headers.update({
            'User-Agent': 'dotcloud/cli (version: {0})'.format(version),
            'X-DotCloud-Version': version
        })
        info_str = ''
        try:
            req.request('GET', query, headers = headers)
            resp = req.getresponse()
            info = resp.getheader('X-DotCloud-Info')
            data = resp.read()
            req.close()
            if info:
                self.logger.warning(info.replace(';', '\n'))
            data = json.loads(data)
            if 'data' in data and len(data['data']) > 0:
                info_str = data['data']
        except Exception, exc:
            data = None
            self.logger.error(exc)
        finally:
            try:
                req.close()
            except Exception:
                pass
        match_obj = re.match(
            '([^\n]+\n)+memory:.*[(](?P<usage>\d+)[%][)]', info_str
        )
        if (not data) or data['type'] != 'success' or not match_obj:
            return {}
        return match_obj.groupdict()

    def get_project_name(self):
        """Parse out dotcloud project name from environment.json."""
        env_config = load_config(self.dotcloud_env_path)
        return env_config.get('DOTCLOUD_PROJECT', "")

    def get_services(self):
        """Parse out dotcloud service names from environment.json."""
        services = []
        env_config = load_config(self.dotcloud_env_path)
        for key in env_config.keys():
            match_obj = re.match('^DOTCLOUD_(?P<service>.+)_SSH_URL$', key)
            if match_obj:
                services.append(match_obj.groupdict()['service'].lower())
        return services

    def run(self):
        """The method server-density agent will look for in a plugin."""
        return_dict = {}
        for service in self.get_services():
            serve_dict = self.get_service_info(service)
            memory_usage_val = serve_dict.get('usage', 0)
            memory_usage_key = 'Memory usage in % ({0})'.format(
                service.capitalize()
            )
            return_dict[memory_usage_key] = int(memory_usage_val)
        return return_dict

