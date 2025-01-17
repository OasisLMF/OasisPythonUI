import streamlit as st

class RefreshHandler:
    q_name = "refresh_1"
    refresh_bool = "refreshing"

    def __init__(self, client_interface, interval=None):
        self.client_interface = client_interface

        if interval is None:
            interval = '5s'

        self.interval = interval

        # Set up session state
        self.set_up()

    @staticmethod
    def start(analysis_id, required_status):
        RefreshHandler.add_to_queue(analysis_id, required_status)
        RefreshHandler.set_refresh_bool(True)
        st.rerun()

    @staticmethod
    def get_queue():
        return st.session_state[RefreshHandler.q_name]

    @staticmethod
    def is_refreshing():
        return st.session_state[RefreshHandler.refresh_bool]

    @staticmethod
    def set_refresh_bool(state=True):
        st.session_state[RefreshHandler.refresh_bool] = state

    @staticmethod
    def add_to_queue(analysis_id, required_status):
        st.session_state[RefreshHandler.q_name].append((analysis_id, required_status))

    @staticmethod
    def set_up():
        if RefreshHandler.q_name not in st.session_state:
            st.session_state[RefreshHandler.q_name] = []
        if RefreshHandler.refresh_bool not in st.session_state:
            st.session_state[RefreshHandler.refresh_bool] = False

    @staticmethod
    def queue_empty():
        return len(RefreshHandler.get_queue()) == 0

    def update_queue(self):
        st.session_state[RefreshHandler.q_name] = self.clear_rerun_queue()

        if RefreshHandler.queue_empty() and RefreshHandler.is_refreshing():
            RefreshHandler.set_refresh_bool(False)
            st.rerun()

    def run_every(self):
        run_every=None
        if not RefreshHandler.queue_empty():
            run_every = self.interval

        return run_every

    def clear_rerun_queue(self):
        q = self.get_queue()
        while True:
            if len(q) == 0:
                return []

            id, required_status = q.pop(0)
            if not (self.client_interface.analyses.get(id)['status'] == required_status):
                q.insert(0, (id, required_status))
                return q
