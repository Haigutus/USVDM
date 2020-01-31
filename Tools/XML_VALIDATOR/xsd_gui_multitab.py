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

    dcc.Store(id='xml_data', data="test_xml"),
    dcc.Store(id='xsd_data', data="test_xsd"),


    dcc.Tabs(children=[
        html.Div([
        dcc.Tab(label='XML', children = [
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
        ])]),

        html.Div([
        dcc.Tab(label='XSD', children = [
            ace_components.Ace(

                id='xsd',
                focus=True,
                mode='xml',
                theme='monokai',
                className = "col-sm",
                cursorStart = 1,
                style= {"width":"100%", "height":"100vh"},
                fontSize = 14,
                value= "Copy your XSD here",
                showGutter = True,
                highlightActiveLine = True,

            )
        ])])


    ])
],className="container-fluid")


# https://community.plot.ly/t/sharing-a-dataframe-between-tabs/7334/3
# https://dash.plot.ly/dash-core-components/store

@app.callback(Output('xml_data', 'data'),
              [Input('xml', 'value')])
def update_xml(xml_string):
    return {"value":xml_string}

@app.callback(Output('xsd_data', 'data'),
              [Input('xsd', 'value')])
def update_xml(xsd_string):
    return {"value":xml_string}


@app.callback(Output('error_log', 'value'),
              [Input('xml_data', 'data'),
               Input('xsd_data', 'data')])
def display_output(xml_string, xsd_string): # TODO higlight erronous rows in xml editor

    if xsd_string == "Copy your XSD here" or "":
        xsd_string = False

    status_list = xsd.validate_XML_string(xml_string, xsd_string)

    status_string = ""

    for item in status_list:
        status_string += "{} -> {}\n".format(item["type"], item["status"])


        if item["type"] == "Validation":

            for error in item["errors"]:
                status_string += "line {} - {}\n".format(error["line"], error["message"])

        else:
            for error in item["errors"]:
                status_string += "{}\n".format(error)

    return status_string

if __name__ == '__main__':
    app.run_server(debug=False, host= '0.0.0.0', port=8020)



