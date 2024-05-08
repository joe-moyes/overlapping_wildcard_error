# -*- coding: utf-8 -*-
"""
Created on Tue May  7 19:24:10 2024

@author: Joseph.Moyes
"""

from dash import Dash, dcc, html, callback, callback_context, Output, Input, State, MATCH, ALL, no_update
import dash_bootstrap_components as dbc
import json
import regex as re

app = Dash(
    __name__, 
    external_stylesheets = [dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions = True # does not suppress 'overlapping widlcard outputs' error
    )
application = app.server

############################################################################### 
# 1. Component objects used to populate a filter menu
###############################################################################

class MarkdownInFilterFooter(dcc.Markdown):
    
    class ids:
        
        markdown_name = lambda A_or_B, var_type, variable: {
            'component': 'MarkdownInFilterFooter',
            'name_or_value' : 'name',
            'A_or_B' : A_or_B,
            'var_type' : var_type,
            'variable': variable
        }
        
        markdown_value = lambda A_or_B, var_type, variable: {
            'component': 'MarkdownInFilterFooter',            
            'name_or_value' : 'value',
            'A_or_B' : A_or_B,        
            'var_type' : var_type,
            'variable': variable
        }

    ids = ids
    
    def __init__(self, A_or_B, var_type, variable, name_or_value):
        """
        Markdown component that will show what value(s) are currently selected
        for a given variable in the filter menu.
        
        - A_or_B: string, denotes whether the instance belongs to the filter menu of Audience 
            A or Audience B.
        - var_type: string, denotes what variable type the instance belongs to:
            'D': discrete/dropdown variable
            'R': ratio/rangeslider variable
            This avoids an 'overlapping wildcard callback outputs' error caused by
            the markdown_children_update() method of both FormWithRadioitemsAndDropdown
            and FormWithRadioitemsAndRangeslider, respectively.
        - variable: string, denotes which variable this component is built for. Together, 
            the combination of A_or_B and variable must be unique to a given instance.
            variable is also assigned to the children property of button.                    
        """
        # id:
        id_ = self.ids.markdown_name(A_or_B, var_type, variable) if name_or_value == 'name' \
            else self.ids.markdown_value(A_or_B, var_type, variable)
        
        if var_type not in ['D', 'R']:
            raise ValueError("var_type should be one of ['D', 'R']")
        
        # classname:
        className = "text-primary" if A_or_B == "A" else "text-secondary" 
        
        # children:
        if name_or_value == 'name':
            children = f"**&nbsp;{variable}:&nbsp;**"
        else:
            children = "All"
        
        super().__init__(
            children,
            id = id_,
            className = className if name_or_value == 'name' else "",
            style = {"height" : "1rem"}
            )
            
    @callback(
        Output(ids.markdown_value(MATCH, MATCH, MATCH), 'className'),
        Input(ids.markdown_value(MATCH, MATCH, MATCH), 'children'),
        prevent_initial_call = True
        )
    def markdown_value_color_update(markdown_value):     
        return "" if markdown_value == "All" else "text-info"


class FormWithRadioitemsAndDropdown(dbc.Form):

    class ids:
        
        # button that toggles collapse
        button = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndDropdown',
            'subcomponent': 'button',
            'A_or_B' : A_or_B,            
            'variable': variable
            }
        
        # collapse that wraps radioitems and dropdown
        collapse = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndDropdown',
            'subcomponent': 'collapse',
            'A_or_B' : A_or_B,
            'variable': variable
            }        
        
        # radioitem per variable filter option
        radioitems = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndDropdown',
            'subcomponent': 'radioitems',
            'A_or_B' : A_or_B,            
            'variable': variable
            }
                
        # dropdown of all variable values
        dropdown = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndDropdown',
            'subcomponent': 'dropdown',
            'A_or_B' : A_or_B,            
            'variable': variable
            }

    ids = ids
        
    def __init__(
        self,
        A_or_B,
        variable,
        radioitem2dropdownvalues_dict
        ):
        """FormWithRadioitemsAndDropdown is composed of button and collapse. The button 
        opens/closes collapse, which contains radioitems and dropdown. 
        
        The button shows the variable name. Inside the collapse, the radioitems are determined
        by keys of radioitem2dropdownvalues_dict and the dropdown options are determined by the 
        value of radioitem2dropdownvalues_dict where key equals 'All'.
        
        radioitem2dropdownvalues_dict is a dictionary that specifies which radioitem option 
        corresponds to which dropdown options, which is stored in the store component. 
        
        - A_or_B: string, denotes whether the instance belongs to the filter menu of Audience 
            A or Audience B.
        - variable: string, denotes which variable this component is built for. Together, 
            the combination of A_or_B and variable must be unique to a given instance.
            variable is also assigned to the children property of button.     
        - radioitem2dropdownvalues_dict: dictionary of {radioitem value: dropdown values,
                                                        ...}
        """
                
        className = "text-primary" if A_or_B == "A" else "text-secondary"
        color = className
                
        try:
            dropdown_options = radioitem2dropdownvalues_dict['All']
        except KeyError:
            raise KeyError("radioitem2dropdownvalues_dict does not contain a key named " +
                           "'All'. This is required to specify dropdown options.")

        radioitem_options = ['All'] + [x for x in radioitem2dropdownvalues_dict.keys()
                                       if x != 'All']
        
        # layout:
        super().__init__(
            [
                dbc.Button(
                    variable,
                    id =  self.ids.button(A_or_B, variable),
                    color = 'link',
                    className = className,
                    size = 'md',
                    n_clicks = 0
                    ),
                
                dbc.Collapse(
                    [
                        dbc.RadioItems(
                            id = self.ids.radioitems(A_or_B, variable),
                            options = [
                                {'label': i, 'value' : i}
                                for i in radioitem_options
                                ],
                            value = 'All',
                            inline = True,
                            labelStyle = {
                                "font-size" : 'small',
                                "color" : color
                                }
                            ),
                        dcc.Dropdown(
                            id = self.ids.dropdown(A_or_B, variable),
                            multi = True,
                            options = dropdown_options,
                            value = dropdown_options,
                            className = 'dash-bootstrap',
                            style = {
                                "font-size" : 'small',
                                "color" :  color
                                }
                            )
                        ],
                    id = self.ids.collapse(A_or_B, variable),
                    is_open = False
                    )
                ]
            )
    
    @callback(
        Output(ids.collapse(MATCH, MATCH), 'is_open'),        
        Input(ids.button(MATCH, MATCH), 'n_clicks'),
        State(ids.collapse(MATCH, MATCH), 'is_open'),
        prevent_initial_call = True
        )
    def toggle_collapse(n_clicks, is_open):
        return not is_open
    
    @callback(
        Output(ids.dropdown(MATCH, MATCH), 'value'),
        Output(ids.dropdown(MATCH, MATCH), 'options'),
        
        Output(ids.radioitems(MATCH, MATCH), 'value'),
        
        Input(ids.radioitems(MATCH, MATCH), 'value'),
        
        Input(ids.dropdown(MATCH, MATCH), 'value'),
        
        State('Store-ProjectVariableSyncDicts', 'data'),        
        prevent_initial_call = True
        )
    def sync_radioitems_and_dropdown(radioitems_value, dropdown_value, store_data):
        ctx = callback_context
        trigger_id_dict = list(ctx.triggered_prop_ids.values())[0]
        sync_dict = json.loads(store_data)[trigger_id_dict['variable']]
        
        if trigger_id_dict['subcomponent'] == 'radioitems':
            dropdown_value = sync_dict[radioitems_value]
            dropdown_options = [{'label':i, 'value':i}
                                for i in dropdown_value]
            
        else: 
            for k, v in sync_dict.items():
                if sorted(v) == sorted(dropdown_value):
                    radioitems_value = k
                    break
            else:
                radioitems_value = None
            dropdown_options = no_update  
            
        return dropdown_value, dropdown_options, radioitems_value
           
    @callback(
        output = dict(
            markdown_children_A = Output(MarkdownInFilterFooter.ids.markdown_value('A', 'D', MATCH), 'children'),
            markdown_children_B = Output(MarkdownInFilterFooter.ids.markdown_value('B', 'D', MATCH), 'children')
            ),
        inputs = dict(
            dropdown_value = Input(ids.dropdown(ALL, MATCH), 'value'),
            store_data = State('Store-ProjectVariableSyncDicts', 'data'),
            not_audience_A = State({'component' : 'Checkbox-NotAudienceA', 'A_or_B' : 'B'}, 'value'),
            ),
        prevent_initial_call = True,
        allow_duplicate = True
        )
    def markdown_children_update(dropdown_value, store_data, not_audience_A):
        A_or_B = next(iter(callback_context.triggered_prop_ids.values()))['A_or_B']
        variable = next(iter(callback_context.triggered_prop_ids.values()))['variable']
        dropdown_value = next(iter(callback_context.triggered))['value']
        store_data = callback_context.args_grouping.store_data['value']
        not_audience_A = callback_context.args_grouping.not_audience_A['value']
        
        if not dropdown_value: 
            markdown_children = "-"
        else:
            sync_dict = json.loads(store_data)[variable]
            
            for k, v in sync_dict.items():
                if sorted(v) == sorted(dropdown_value):
                    markdown_children = k
                    break
            else:
                markdown_children = ", ".join(dropdown_value)
               
        if A_or_B == 'B':
            markdown_children_B = markdown_children
            markdown_children_A = no_update
        else:
            markdown_children_A = markdown_children
            markdown_children_B = 'NOT '+markdown_children if not_audience_A else no_update
            
        return dict(markdown_children_A = markdown_children_A, 
                    markdown_children_B = markdown_children_B) 
            
    
class FormWithRadioitemsAndRangeslider(dbc.Form):

    class ids:
        
        # button that toggles collapse
        button = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndRangeslider',
            'subcomponent': 'button',
            'A_or_B' : A_or_B,            
            'variable': variable
            }
        
        # collapse that wraps radioitems and dropdown
        collapse = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndRangeslider',
            'subcomponent': 'collapse',
            'A_or_B' : A_or_B,
            'variable': variable
            }        
        
        # radioitem per variable filter option
        radioitems = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndRangeslider',
            'subcomponent': 'radioitems',
            'A_or_B' : A_or_B,            
            'variable': variable
            }
                
        # rangeslider for variable min - max
        rangeslider = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndRangeslider',
            'subcomponent': 'rangeslider',
            'A_or_B' : A_or_B,            
            'variable': variable
            }
        
        # store for radioitem2rangeslidervalues_dict
        store = lambda A_or_B, variable: {
            'component': 'FormWithRadioitemsAndRangeslider',
            'subcomponent': 'store',
            'A_or_B' : A_or_B,            
            'variable': variable
            }

    ids = ids
        
    def __init__(
        self,
        A_or_B,
        variable,
        radioitem2rangeslidervalues_dict,
        ):
        """FormWithRadioitemsAndRangeslider is composed of button and collapse. The button 
        opens/closes collapse, which contains radioitems and rangeslider. 
        
        The button shows the variable name. Inside the collapse, the radioitems are determined
        by the keys of radioitem2rangeslidervalues_dict and the rangeslider kwargs are determined 
        by rangeslider_kwargs. The initial rangeslider value is determined by the value of the 
        key:value pair in radioitem2rangeslidervalues_dict where key equals 'All'.
        
        radioitem2rangeslidervalues_dict is a dictionary that specifies which radioitem option 
        corresponds to a rangeslider value, which is stored in the store component. 
        
        - A_or_B: string, denotes whether the instance belongs to the filter menu of Audience 
        A or Audience B.
        - variable: string, denotes which variable this component is built for. Together, 
        the combination of A_or_B and variable must be unique to a given instance.       
        - radioitem2rangeslidervalues_dict: dictionary of {radioitem value: [x1,x2],
                                                           ...}
        - rangeslider_kwargs: dict, assigns values (dict values) to rangeslider properties
        (dict keys). This should include values for min and max.
        """
                
        className = "text-primary" if A_or_B == "A" else "text-secondary"
        color = className
                
        try:
            rangeslider_range = radioitem2rangeslidervalues_dict['All']
        except KeyError:
            raise KeyError("radioitem2rangeslidervalues_dict does not contain a key named " +
                           "'All'. This is required to specify initial rangeslider value.")
        
        radioitem_options = ['All'] + [x for x in radioitem2rangeslidervalues_dict.keys()
                                       if x != 'All']
        
        marks_format = '${:,}' if re.match('^[Ii]', variable) else '{}'
            
        # layout:
        super().__init__(
            [
                dbc.Button(
                    variable,
                    id =  self.ids.button(A_or_B, variable),
                    color = 'link',
                    className = className,
                    size = 'md',
                    n_clicks = 0
                    ),
                
                dbc.Collapse(
                    [
                        dbc.RadioItems(
                            id = self.ids.radioitems(A_or_B, variable),
                            options = [
                                {'label': i, 'value' : i}
                                for i in radioitem_options
                                ],
                            value = radioitem_options[0],
                            inline = True,
                            labelStyle = {
                                "font-size" : 'small',
                                "color" : color
                                }
                            ),                
                
                        dcc.RangeSlider(
                            id = self.ids.rangeslider(A_or_B, variable),
                            value = rangeslider_range,
                            allowCross = False,
                            tooltip = {
                                'always_visible' : False, 
                                'placement' : 'bottom'
                                },
                            updatemode = 'mouseup',
                            className = "dash-bootstrap",
                            min =  rangeslider_range[0],
                            max = rangeslider_range[1],
                            step = 1000 if rangeslider_range[1] > 100000 else 1,
                            marks = {
                                i : marks_format.format(i) 
                                for i in rangeslider_range
                                }
                            )
                        ],
                    id = self.ids.collapse(A_or_B, variable),
                    is_open = False
                    )        
                ]
            )
    
    @callback(
        Output(ids.collapse(MATCH, MATCH), 'is_open'),        
        Input(ids.button(MATCH, MATCH), 'n_clicks'),
        State(ids.collapse(MATCH, MATCH), 'is_open'),
        prevent_initial_call = True
        )
    def toggle_collapse(n_clicks, is_open):
        return not is_open
    
    @callback(
        Output(ids.rangeslider(MATCH, MATCH), 'value'),        
        Output(ids.radioitems(MATCH, MATCH), 'value'),
        
        Input(ids.radioitems(MATCH, MATCH), 'value'),
        Input(ids.rangeslider(MATCH, MATCH), 'value'),
        
        State('Store-ProjectVariableSyncDicts', 'data'),        
        prevent_initial_call = True
        )
    def sync_radioitems_and_rangelsider(radioitems_value, rangeslider_value, store_data):
        ctx = callback_context
        trigger_id_dict = list(ctx.triggered_prop_ids.values())[0]
        sync_dict = json.loads(store_data)[trigger_id_dict['variable']]
        
        if trigger_id_dict['subcomponent'] == 'radioitems':
            rangeslider_value = sync_dict[radioitems_value]
        
        else: 
            for k, v in sync_dict.items():
                if v == rangeslider_value:
                    radioitems_value = k
                    break
            else:
                radioitems_value = None
            
        return rangeslider_value, radioitems_value

    @callback(
        output = dict(
            markdown_children_A = Output(MarkdownInFilterFooter.ids.markdown_value('A', 'R', MATCH), 'children'),
            markdown_children_B = Output(MarkdownInFilterFooter.ids.markdown_value('B', 'R', MATCH), 'children')
            ),
        inputs = dict(
            rangeslider_value = Input(ids.rangeslider(ALL, MATCH), 'value'),
            store_data = State('Store-ProjectVariableSyncDicts', 'data'),
            not_audience_A = State({'component' : 'Checkbox-NotAudienceA', 'A_or_B' : 'B'}, 'value'),
            ),
        prevent_initial_call = True,
        allow_duplicate = True
        )
    def markdown_children_update(rangeslider_value, store_data, not_audience_A):
        A_or_B = next(iter(callback_context.triggered_prop_ids.values()))['A_or_B']
        variable = next(iter(callback_context.triggered_prop_ids.values()))['variable']
        rangeslider_value = next(iter(callback_context.triggered))['value']
        store_data = callback_context.args_grouping.store_data['value']
        not_audience_A = callback_context.args_grouping.not_audience_A['value']
       
        sync_dict = json.loads(store_data)[variable]
        
        for k, v in sync_dict.items():
            if v == rangeslider_value:
                markdown_children = k
                break
        else:
            markdown_children = "{:,} - {:,}".format(
                rangeslider_value[0], rangeslider_value[1])
               
        if A_or_B == 'B':
            markdown_children_B = markdown_children
            markdown_children_A = no_update
        else:
            markdown_children_A = markdown_children
            markdown_children_B = 'NOT '+markdown_children if not_audience_A else no_update
            
        return dict(markdown_children_A = markdown_children_A, 
                    markdown_children_B = markdown_children_B) 


############################################################################### 
# 2. Function to build a filter menu
###############################################################################

def card_filtermenu(A_or_B):
    audience_A = True if A_or_B == 'A' else False
        
    if audience_A:
        form_not_audience_A = None
    else:        
        form_not_audience_A = dbc.Form(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label(
                            "Not Audience A ",
                            size = "md",
                            className = "text-secondary",
                            style = {'paddingLeft' : '12px'} 
                            ), 
                        width = "auto"
                        ),
                    dbc.Col(
                        dbc.Checkbox(
                            id = {
                                'component' : 'Checkbox-NotAudienceA',
                                'A_or_B' : 'B'
                                },
                            value = False,
                            style = {
                                'position' : 'relative',
                                'top' : '10px'
                                }
                            ), 
                        width = "auto"
                        )
                    ]
                )
            )
    
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                f"Audience {A_or_B}",
                                id = {
                                    'component' : 'Button-OpenFilterOptions',
                                    'A_or_B' : A_or_B
                                    },
                                color = 'link',
                                className = "text-primary" if audience_A else "text-secondary",
                                size = 'lg',
                                n_clicks = 0,
                                disabled = False if audience_A else True
                                )
                            ),
                        dbc.Col(
                            # Not visible if Audience A. It is created regardless to 
                            # allow use of MATCH in the callback expand_or_collapse_filtermenu().
                            dbc.Checkbox(
                                id = {
                                    'component' : 'Checkbox-AudienceB',
                                    'A_or_B' : A_or_B
                                    },
                                value = False,
                                style = {
                                    "display" : "inline" if not audience_A else "none",
                                    'position' : 'relative',
                                    "top" : "11px",
                                    "right" : "15rem"
                                    }
                                )
                            )
                        ],
                    className = "h-100"
                    ),            
                style = {
                    "height" : "3rem", 
                    "padding" : '0rem'
                    }
                ),
            
            dbc.Collapse(
                dbc.CardBody(
                    [
                        html.Div(
                            id = {
                                'component' : 'CardBody-FilterOptions',
                                'A_or_B' : A_or_B
                                }
                            ),
                        form_not_audience_A
                        ]
                    ),
                id = {
                    'component' : 'Collapse-FilterOptions',
                    'A_or_B' : A_or_B
                    },
                is_open = False
                ),
            
            dbc.CardFooter(
                id = {
                    'component' : 'CardFooter-FilterSummaries',
                    'A_or_B' : A_or_B
                    },  
                style = {
                    "display" : "flex",
                    "flexWrap" : "wrap",
                    "overflow-y" : "scroll",
                    "fontSize" : "small",
                    "padding" : "2px",
                    "height" : "100%"
                    }
                )
            ]
        )


@callback(
    Output({'component' : 'Collapse-FilterOptions', 'A_or_B' : MATCH}, 'is_open'),
    Output({'component' : 'Button-OpenFilterOptions', 'A_or_B' : MATCH}, 'disabled'),
    Input({'component' : 'Button-OpenFilterOptions', 'A_or_B' : MATCH}, 'n_clicks'),
    Input({'component' : 'Checkbox-AudienceB', 'A_or_B' : MATCH}, 'value'),
    State({'component' : 'Collapse-FilterOptions', 'A_or_B' : MATCH}, 'is_open'),
    prevent_initial_call = True
)
def expand_or_collapse_filtermenu(button, checkbox, is_open):
    ctx = callback_context
    if next(iter(ctx.triggered_prop_ids.values()))['component'] == 'Button-OpenFilterOptions':
        return not is_open, no_update
    else:
        return False, not checkbox


# below callback is origin of the error: "Overlapping wildcard callback outputs"
# I have commented it out so you can first run this example app successfully.
# @callback(
#     output = dict(
#         discrete_variable_buttons = Output(
#             FormWithRadioitemsAndDropdown.ids.button(MATCH, ALL), 'disabled'
#             ),
#         numeric_variable_buttons = Output(
#             FormWithRadioitemsAndRangeslider.ids.button(MATCH, ALL), 'disabled'
#             ),
#         markdown_values_B = Output(
#             MarkdownInFilterFooter.ids.markdown_value(MATCH, ALL, ALL), 'children'
#             )
#         ),
#     inputs = dict(
#         not_audience_A = Input(
#             {'component' : 'Checkbox-NotAudienceA', 'A_or_B' : MATCH}, 'value'
#             ),
#         markdown_values_A = State(
#             MarkdownInFilterFooter.ids.markdown_value('A', ALL, ALL), 'children'
#             )
#         ),
#     prevent_initial_call = True,
#     allow_duplicate = True
#     )
# def if_not_audience_A_checked(
#         not_audience_A, 
#         markdown_values_A):
    
#     # the below is just placeholder code to indicate the gist of what I want:
#     # if the 'Not Audience A' checkbutton is checked, I want to update all
#     # Audience B markdown components to reference the values of the Audience A 
#     # markdown components.
    
#     if not_audience_A:
#         markdown_values_B = list(map(lambda value: f'NOT {value}', markdown_values_A))
#     else:
#         markdown_values_B = no_update
    
#     return dict(
#         discrete_variable_buttons = not not_audience_A,
#         numeric_variable_buttons = not not_audience_A,
#         markdown_values_B = markdown_values_B
#         )


############################################################################### 
# 3. Layout
###############################################################################

FILTER_MENUS = dbc.Row(
    [
        dbc.Col(
            card_filtermenu('A'), 
            width = 6
            ),
        dbc.Col(
            card_filtermenu('B'), 
            width = 6
            ),
        ], 
    className = "g-0"
    )

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    id = 'Dropdown-SelectedProject',
                    options = [
                        dict(label=project_name, value=project_name)
                        for project_name in ['Project 1']
                        ],
                    value = 'Project 1',
                    multi = False,
                    clearable = False,
                    )
                )
            ),
         dbc.Row(
            dbc.Col(
                FILTER_MENUS,
                ),
            ),
        dcc.Store(
            id = 'Store-ProjectVariableSyncDicts'
            )
        ], 
    fluid = True
    )

############################################################################### 
# 4. For demonstration purposes
###############################################################################

@callback(
    Output({'component' : 'CardBody-FilterOptions', 'A_or_B' : 'A'}, 'children'),
    Output({'component' : 'CardFooter-FilterSummaries', 'A_or_B' : 'A'}, 'children'),
    Output({'component' : 'CardBody-FilterOptions', 'A_or_B' : 'B'}, 'children'),
    Output({'component' : 'CardFooter-FilterSummaries', 'A_or_B' : 'B'}, 'children'),
    Output('Store-ProjectVariableSyncDicts', 'data'),
    Input('Dropdown-SelectedProject', 'value')
    )
def initiate_a_demo(selected_project):
    
    radioitem_options_Market = {
        'All' : ['UK', 'Germany', 'Canada', 'USA', 'India', 'China'],
        'Europe' : ['UK', 'Germany'],
        'North America' : ['Canada', 'USA'],
        'Asia' : ['India', 'China']
        }
                   
    radioitem_options_Age = {
        'All' : [1, 100],
        'Bottom 25%' : [1, 25],
        'Bottom 50%' : [1, 50],
        'Top 50%' : [50, 100],
        'Top 25%' : [75, 100]
        }
    
    store_sync_dicts = {
        'Market' : radioitem_options_Market,
        'Age' : radioitem_options_Age
        }
    
    filtermenu_A_components = [
        FormWithRadioitemsAndDropdown(
            'A',
            'Market',
            radioitem_options_Market
            ),
        FormWithRadioitemsAndRangeslider(
            'A',
            'Age',
            radioitem_options_Age
            )
        ]
    
    filtermenu_B_components = [
        FormWithRadioitemsAndDropdown(
            'B',
            'Market',
            radioitem_options_Market
            ),
        FormWithRadioitemsAndRangeslider(
            'B',
            'Age',
            radioitem_options_Age
            )
        ]
          
    filterfooter_A_components = [
        MarkdownInFilterFooter(
            'A',
            'D',
            'Market',
            'name'
            ),
        MarkdownInFilterFooter(
            'A',
            'D',
            'Market',
            'value'
            )    ,
        MarkdownInFilterFooter(
            'A',
            'R',
            'Age',
            'name'
            ),
        MarkdownInFilterFooter(
            'A',
            'R',
            'Age',
            'value'
            )      
        ]
    
    filterfooter_B_components = [
        MarkdownInFilterFooter(
            'B',
            'D',
            'Market',
            'name'
            ),
        MarkdownInFilterFooter(
            'B',
            'D',
            'Market',
            'value'
            )    ,
        MarkdownInFilterFooter(
            'B',
            'R',
            'Age',
            'name'
            ),
        MarkdownInFilterFooter(
            'B',
            'R',
            'Age',
            'value'
            )      
        ]

    return [
        filtermenu_A_components, 
        filterfooter_A_components, 
        filtermenu_B_components,
        filterfooter_B_components,
        json.dumps(store_sync_dicts)
        ]


if __name__ == "__main__":
    app.run_server(debug = True, use_reloader = False)