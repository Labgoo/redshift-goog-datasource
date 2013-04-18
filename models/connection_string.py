import mongo, logging

class ConnectionString():
    @classmethod
    def execute(cls, name, data):
        logging.info('executing transformer %s', name)
        data_explorer = mongo.get_mongo()
        if data_explorer:
            transformer = data_explorer.transformers.find_one({"name": name})

        if not transformer:
            return data

        code = transformer.get('code')

        code_globals = {}
        code_locals = {'data': data}
        code_object = compile(code, '<string>', 'exec')
        exec code_object in code_globals, code_locals

        return code_locals['result']
