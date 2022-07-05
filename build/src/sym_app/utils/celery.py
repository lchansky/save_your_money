from sym_app.tasks import write_currencies_to_json, update_currencies_db


class TaskManager:
    @staticmethod
    def update_currencies():
        update_currencies_db.delay()
        write_currencies_to_json.delay()

