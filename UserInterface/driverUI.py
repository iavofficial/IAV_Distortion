from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

###--- Driver1 ---###
@app.route('/driver1')
def home_driver1():
    return render_template('driver_index.html')

@app.route('/slider', methods=['POST'])
def slider_driver1():
    value = request.form['value']
    print(f"Driver1: Schieberegler-Wert: {value}")
    return '', 204

@app.route('/changeLane_left', methods=['POST'])
def laneChange_left_driver1():
    print("Driver1: Button << wurde gedrückt!")
    # Hier können Sie Ihren Python-Code hinzufügen, der ausgeführt werden soll, wenn der Button 1 gedrückt wird.
    return redirect(url_for('home_driver1'))

@app.route('/changeLane_right', methods=['POST'])
def changeLane_right_driver1():
    print("Driver1: Button >> wurde gedrückt!")
    # Hier können Sie Ihren Python-Code hinzufügen, der ausgeführt werden soll, wenn der Button 2 gedrückt wird.
    return redirect(url_for('home_driver1'))


# ###--- driver2 ---#
# @app.route('/driver2')
# def home_driver2():
#     return render_template('driver_index.html')
#
# @app.route('/slider', methods=['POST'])
# def slider_driver2():
#     value = request.form['value']
#     print(f"Driver2: Schieberegler-Wert: {value}")
#     return '', 204
#
# @app.route('/changeLane_left', methods=['POST'])
# def laneChange_left_driver2():
#     print("Driver2: Button << wurde gedrückt!")
#     # Hier können Sie Ihren Python-Code hinzufügen, der ausgeführt werden soll, wenn der Button 1 gedrückt wird.
#     return redirect(url_for('home_driver2'))
#
# @app.route('/changeLane_right', methods=['POST'])
# def changeLane_right_driver2():
#     print("Driver2: Button >> wurde gedrückt!")
#     # Hier können Sie Ihren Python-Code hinzufügen, der ausgeführt werden soll, wenn der Button 2 gedrückt wird.
#     return redirect(url_for('home_driver2'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')