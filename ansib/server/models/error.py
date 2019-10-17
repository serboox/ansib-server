from flask_restplus import fields as fr_fields


def error(ns, code, exception):
    error_fields = {
        'exception': fr_fields.String(
            example='Traceback (most recent call last):...'
        ),
        'msg': fr_fields.String(
            example='Unexpected failure during module execution.',
        ),
        'stdout': fr_fields.String(
            example=exception,
        ),
        '_ansible_no_log': fr_fields.Boolean(
            example=False,
        )
    }
    return ns.model('ErrorResponse_{}'.format(code), error_fields)
