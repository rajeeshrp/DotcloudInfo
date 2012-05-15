=============
DotcloudInfo
=============

---------------------------------------------------------
A server-density plugin for monitoring dotcloud services
---------------------------------------------------------

Dotcloud_ helps us to deploy our cloud-based web applications and Server-density_
is a platform used to monitor web-servers. You can install server-density agent
in dotcloud services but as of now, it generates incorrect information regarding 
memory usage etc. This may be due to the way the dotcloud services are deployed.
Dotcloud services are virtual os images sharing the same set of hardwares. So don't
get surprised when the server-density agent reports that, memory of the sort, say 32GB,
is available for a service while in reality, each service enjoys just 512MB by default.
This plugin works to get the exact information using dotcloud api. As of now, only
the memory usage can be tracked.

Installation
=============

* Open an account with Server-density_, if you have not already done that.

* Install server-density agent in at least one of your dotcloud services.
  The documentation at http://docs.dotcloud.com/tutorials/more/serverdensity/ 
  describes the steps involved in the manual installation.

* Copy your local api-key file (Usually named as `doctcloud.conf`) to the service 
  where you've installed the server-density agent. ::

    dotcloud run myapp.myservice "mkdir ~/.dotcloud"
    dotcloud run myapp.myservice "cat > ~/.dotcloud/dotcloud.conf" < ~/.dotcloud/dotcloud.conf

* Install this plugin to the service. If you are doing this manually, ssh into
  your service, create a plugins directory and copy this script there. Follow the
  instructions available at the Server-density_ site for installing a plugin.

* Restart the server-density agent.

.. _Dotcloud: http://www.dotcloud.com

.. _Server-density: http://www.serverdensity.com
