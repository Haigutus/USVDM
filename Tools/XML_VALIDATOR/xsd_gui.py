import dash
import dash_core_components as dcc
import dash_html_components as html
import ace_components
from dash.dependencies import Input, Output, State

from lxml import etree

import xsd

from tools import *


app = dash.Dash()

external_css = ["https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
                "https://maxcdn.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css", ]

for css in external_css:
    app.css.append_css({"external_url": css})

external_js = [ "https://code.jquery.com/jquery-3.3.1.min.js",
                "https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js",
                "https://maxcdn.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js"]

for js in external_js:
    app.scripts.append_script({"external_url": js})


app.layout = html.Div(children=[

    html.Div(children = [
    ace_components.Ace(

        id='xml',
        focus=True,
        mode='xml',
        theme='monokai',
        className = "col-sm",
        cursorStart = 1,
        style= {"width":"100%", "height":"80vh"},
        fontSize = 14,
        value= "Copy your IEC62325 or EDIGAS 5 XML message here",
        showGutter = True,
        highlightActiveLine = True,

    ),

    ace_components.Ace(
        id='error_log',
        focus=False,
        mode='Text',
        theme='monokai',
        className = "col-sm",
        style= {"width":"100%", "height":"20vh"},
        fontSize = 14,
        value= "",

    )
    ])
],className="container-fluid")

@app.callback(Output('error_log', 'value'),
              [Input('xml', 'value')])
def display_output(content): # TODO higlight erronous rows in xml editor


    errors_list = xsd.validate_XML_string(content)
    errors_string = ""

    if type(errors_list) == list:

        for error in errors_list:
            errors_string += "line {} - {}\n".format(error["line"], error["message"])

    else:
        errors_string = str(errors_list)

    return errors_string

if __name__ == '__main__':
    app.run_server(debug=False, host= '0.0.0.0', port=8020)



