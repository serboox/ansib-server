import functools
import logging

LOG = logging.getLogger(__name__)


def session(session_fn):
    def _get_session(fn):
        @functools.wraps(fn)
        def newfn(*args, **kwargs):
            if kwargs.get('session'):
                return fn(*args, **kwargs)
            else:
                with session_fn() as session:
                    kwargs['session'] = session
                    return fn(*args, **kwargs)

        return newfn

    return _get_session


class BaseRepository(object):
    model_class = None

    def get(self, session, query_options=None, **filters):
        """
        Retrieves an entity from the database.

        :param filters: Filters to decide which entity should be retrieved.
        """
        query = session.query(self.model_class).filter_by(**filters)
        if query_options:
            query = query.options(query_options)
        model = query.first()

        if model:
            return model

    def get_all(self, session, query_options=None, **filters):
        """
        Retrieves a list of entities from the database.

        :param filters: Filters to decide which entities should be retrieved.
        """
        query = session.query(self.model_class).filter_by(**filters)
        if query_options:
            query = query.options(query_options)
        model_list = query.all()
        return model_list

    def create(self, session=None, **data):
        model = self.model_class(**data)
        session.add(model)
        session.flush()
        return model

    def update(self, id, session=None, **data):
        """Updates an entity in the database."""
        session.query(self.model_class).filter_by(id=id).update(data)
        session.flush()

    def delete(self, session=None, **filters):
        """
        Deletes an entity from the database.

        :param filters: Filters to decide which entity should be deleted.
        """
        model = session.query(self.model_class).filter_by(**filters).one()
        session.delete(model)
        session.flush()


class Repositories(object):

    def __init__(self):
        pass
