from flask import Flask, render_template, request, redirect, url_for


class StaffUI:

    def __init__(self, name=__name__):
        self.app = Flask(name)
        return

    def run(self):
        def home_staff_control():
            return render_template('staff_control.html')
        self.app.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)