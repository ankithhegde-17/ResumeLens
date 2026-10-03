"""Models the external workspace.js protocol, not hidden server persistence."""
import json
import re
from flask.testing import FlaskClient
from browser_workspace import BrowserWorkspace

class WorkspaceClient(FlaskClient):
    workspace_state=''
    csrf=''
    def remember(self,response):
        if response.is_json and not response.headers.get('Content-Disposition'):
            self.workspace_state=response.get_json().get('workspace_state',self.workspace_state)
        elif response.mimetype=='text/html':
            html=response.get_data(as_text=True)
            found=re.search(r'<script type="application/json" id="workspace-state">(.*?)</script>',html,re.S)
            if found: self.workspace_state=json.loads(found.group(1))['state']
            found=re.search(r'<meta name="csrf-token" content="([^"]+)"',html)
            if found: self.csrf=found.group(1)
        return response
    def get(self,path,*args,**kwargs):
        if self.workspace_state and not path.startswith('/static/'):
            response=super().open(path,method='POST',json={'workspace_state':self.workspace_state,'csrf_token':self.csrf},headers={'X-Workspace-Read':'1'},*args,**kwargs)
        else: response=super().get(path,*args,**kwargs)
        return self.remember(response)
    def post(self,path,*args,**kwargs):
        data=kwargs.get('data',{})
        if isinstance(data,dict):
            data=dict(data,workspace_state=self.workspace_state)
            kwargs['data']=data
        kwargs['headers']=dict(kwargs.get('headers',{}),**{'X-Workspace-Client':'test'})
        return self.remember(super().post(path,*args,**kwargs))
    def workspace(self):
        with self.session_transaction() as session: visitor=session['visitor']
        return BrowserWorkspace(self.application.config['SECRET_KEY'],visitor,self.workspace_state)

def browser_app(app):
    app.test_client_class=WorkspaceClient
    return app
