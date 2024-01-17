from flask import Flask, request, render_template
import requests
import dropbox
import threading
import json
import os

app = Flask(__name__)

save_path = os.path.join(os.getcwd(), 'save_files')
app.config['UPLOAD_FOLDER'] = save_path

with open(os.path.join(os.getcwd(), 'cursor.json')) as f:
            CURSOR_DATA = json.load(f)
with open(os.path.join(os.getcwd(), 'access_token.json')) as f:
            ACCESS_TOKEN_DATA = json.load(f)
with open(os.path.join(os.getcwd(), 'refresh_token.json')) as f:
            REFRESH_TOKEN_DATA = json.load(f)
with open(os.path.join(os.getcwd(), 'secret.json')) as f:
            SECRET_DATA = json.load(f)

def get_all_exist_files(user_id):
    try:
        DROPBOX_ACCESS_TOKEN = ACCESS_TOKEN_DATA.get(user_id)
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

        all_files = dbx.files_list_folder(path='',recursive=True)
        if len(all_files.entries) != 0:
            for entry in all_files.entries:
                local_directory = os.path.join(app.config['UPLOAD_FOLDER'], os.path.dirname(entry.path_display)[1:])
                local_file_path = os.path.join(local_directory, os.path.basename(entry.path_display))

                if isinstance(entry,dropbox.files.FolderMetadata):
                    os.makedirs(local_file_path, exist_ok=True)
                if isinstance(entry, dropbox.files.FileMetadata): # # Assuming `entry` is the FileMetadata object
                        os.makedirs(local_directory, exist_ok=True)
                        dbx.files_download_to_file(local_file_path, entry.path_display)
        with open("cursor.json", 'w') as f:
                CURSOR_DATA[user_id] = all_files.cursor
                json.dump(CURSOR_DATA, f)
    except Exception as e:
        print("error",e)

def process_updates(account):
    try:    
        DROPBOX_ACCESS_TOKEN = ACCESS_TOKEN_DATA.get(account)

        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

        latest_cursor = dbx.files_list_folder_get_latest_cursor(path='', recursive=True).cursor

        previous_cursor = CURSOR_DATA[account]

        changes = dbx.files_list_folder_continue(previous_cursor)

        for entry in changes.entries:
            local_directory = os.path.join(app.config['UPLOAD_FOLDER'], os.path.dirname(entry.path_display)[1:])
            local_file_path = os.path.join(local_directory, os.path.basename(entry.path_display))

            if isinstance(entry,dropbox.files.FolderMetadata):
                os.makedirs(local_file_path, exist_ok=True)         ## here local_file_path only have to give

            if isinstance(entry, dropbox.files.FileMetadata): # # Assuming `entry` is the FileMetadata object
                client_modified = entry.client_modified
                server_modified = entry.server_modified
                # # Check if the file was uploaded or modified
                if client_modified == server_modified:
                    print(f"The file '{entry.name}' was uploaded.")

                else:
                    print(f"The file '{entry.name}' was modified after being uploaded.")

                os.makedirs(local_directory, exist_ok=True)
                dbx.files_download_to_file(local_file_path, entry.path_display)

            if isinstance(entry,dropbox.files.DeletedMetadata):
                try:
                    os.remove(local_file_path)    
                    print(f"Local file '{local_file_path}' deleted.")
                except FileNotFoundError:
                    print(f"Local file '{local_file_path}' not found.")
                except Exception as e:
                    try: 
                        os.rmdir(local_file_path)
                        print(f"Local folder '{local_file_path}' deleted.") 
                    except Exception as e: 
                        print(f"Error deleting local file '{local_file_path}': {e}")

        with open("cursor.json", 'w') as f:
            CURSOR_DATA[account] = latest_cursor
            json.dump(CURSOR_DATA, f)
        
    except Exception as e:
        if isinstance(e,dropbox.exceptions.AuthError):
            try:
            # Your code to refresh the access token goes here
                print(REFRESH_TOKEN_DATA.get(account), SECRET_DATA.get('DROPBOX_APP_KEY'))
                DROPBOX_TOKEN_URL = 'https://api.dropbox.com/oauth2/token'
                data = {
                    'refresh_token': REFRESH_TOKEN_DATA.get(account),
                    'grant_type': 'refresh_token',
                    'client_id': SECRET_DATA.get('DROPBOX_APP_KEY'),
                    'client_secret': SECRET_DATA.get('DROPBOX_APP_SECRET')
                }
                response = requests.post(DROPBOX_TOKEN_URL, data=data).json()
                print(response)
                with open("access_token.json", 'w') as f:
                    ACCESS_TOKEN_DATA[account] = response.get('access_token')
                    json.dump(ACCESS_TOKEN_DATA, f)
                process_updates(account)
            except Exception as e:
                    print("error",e)
        else:
             print(e)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    # print('Dropbox Webhook Data:', data)
    for account in data['list_folder']['accounts']:
        threading.Thread(target=process_updates, args=(account,)).start()
    return "received"

@app.route('/webhook', methods=['GET'])
def challenge():
    data = request.args.get('challenge')
    return data , 200

@app.route('/home', methods=['GET'])
def home():
    app_key=SECRET_DATA.get('DROPBOX_APP_KEY')
    redirect_uri = SECRET_DATA.get('DROPBOX_redirect_uri')
    return render_template("welcome.html", app_key=app_key, redirect_uri=redirect_uri)
    

@app.route('/auth',methods=['GET'])
def auth():
    authorization_code = request.args.get('code')
    DROPBOX_TOKEN_URL = 'https://api.dropbox.com/oauth2/token'
    data = {
    'code': authorization_code,
    'grant_type': 'authorization_code',
    'client_id':SECRET_DATA.get('DROPBOX_APP_KEY'),
    'client_secret':SECRET_DATA.get('DROPBOX_APP_SECRET'),
    'redirect_uri':SECRET_DATA.get('DROPBOX_redirect_uri')
    }
    response = requests.post(DROPBOX_TOKEN_URL, data=data).json()
    user_id = response.get('account_id')
    access_token = response.get('access_token')
    refresh_token = response.get('refresh_token')
    
    with open("access_token.json",'w') as f:
        ACCESS_TOKEN_DATA[user_id] = access_token
        json.dump(ACCESS_TOKEN_DATA, f)
        
    with open("refresh_token.json",'w') as f:
        REFRESH_TOKEN_DATA[user_id] = refresh_token
        json.dump(REFRESH_TOKEN_DATA, f)
    
    threading.Thread(target=get_all_exist_files, args=(user_id,)).start()
    return {'msg':'Access Granted'}

if __name__ == '__main__':
    app.run(debug=True)

