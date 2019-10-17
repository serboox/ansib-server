# Ansible Server

Ansible server represents a Ansible json based http server. 
He receiving http json page and breaks his for several parts. First 
part contain list of tasks is intended for run in host system. 
Second part contain a list of files with configs which shoul be change.

POST /api/v1/ansible 
Content-Type: application/json
```json
{
  "gather_facts": true,
  "tasks": [
    {
      "name": "Change haproxy config",
      "file": {
        "path": "/tmp/ansib-server/haproxy.cfg",
        "dest": "/etc/haproxy/haproxy.cfg",
        "backup": true
      }
    },
    {
     "name": "Restart and enable haproxy",
      "service": {
        "name": "haproxy",
        "state": "reloaded",
        "enabled": true
      }
    }
  ],
  "files": [
    {
      "path": "/tmp/ansib-server/haproxy.cfg",
      "data": "SGVsbG8gV29ybGQh"
    }
  ]
}
```
Field `files` may be contain several files. Field `data` contain file body in 
base64 encryption.

## Tools
```bash
$ python --version
Python 3.7.3

$ ansible --version
ansible 2.8.4
```

## Ansible
For example response from ansible could be to look like:
```json
[
  {
    "localhost": {
      "msg": "This path where agent is running: /root/python/github.com/serboox/ansib-server",
      "changed": false,
      "_ansible_no_log": false,
      "_ansible_verbose_always": true
    }
  },
  {
    "localhost": {
      "gid": 0,
      "group": "root",
      "size": 12,
      "_ansible_no_log": false,
      "owner": "root",
      "uid": 0,
      "diff": {
        "before": {
          "path": "/tmp/ansib-server/haproxy_new.cfg"
        },
        "after": {
          "path": "/tmp/ansib-server/haproxy_new.cfg"
        }
      },
      "checksum": "2ef7bde608ce5404e97d5f042f95f89f1c232871",
      "invocation": {
        "module_args": {
          "delimiter": null,
          "_original_basename": "haproxy.cfg",
          "serole": null,
          "group": null,
          "regexp": null,
          "access_time_format": "%Y%m%d%H%M.%S",
          "content": null,
          "owner": null,
          "access_time": null,
          "unsafe_writes": null,
          "_diff_peek": null,
          "selevel": null,
          "force": false,
          "attributes": null,
          "mode": null,
          "modification_time": null,
          "remote_src": null,
          "seuser": null,
          "modification_time_format": "%Y%m%d%H%M.%S",
          "backup": null,
          "recurse": false,
          "dest": "/tmp/ansib-server/haproxy_new.cfg",
          "setype": null,
          "directory_mode": null,
          "state": "file",
          "src": null,
          "path": "/tmp/ansib-server/haproxy_new.cfg",
          "follow": true
        }
      },
      "state": "file",
      "mode": "0644",
      "deprecations": [
        {
          "msg": "Distribution Ubuntu 16.04 on host localhost should use /usr/bin/python3, but is using /usr/bin/python for backward compatibility with prior Ansible releases. A future Ansible release will default to using the discovered platform python for this host. See https://docs.ansible.com/ansible/2.8/reference_appendices/interpreter_discovery.html for more information",
          "version": "2.12"
        }
      ],
      "dest": "/tmp/ansib-server/haproxy_new.cfg",
      "changed": false,
      "path": "/tmp/ansib-server/haproxy_new.cfg",
      "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python"
      }
    }
  }
]
```
If execution process will throw an error response would be to looks like:
```json
{
  "localhost": {
    "msg": "ValidationException -> Validation failure: Unsupported request body",
    "exception": "ValueError -> Key 'tasks' not be found in request.",
    "_ansible_no_log": false,
    "stdout": ""
  }
}
```
