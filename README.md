# DropBox Integration

## How to run this flask app:
1. Create a Dropbox app on the [Dropbox website](https://www.dropbox.com/developers/apps/create).
    - Note: Choose the "App Folder" type for accessing a specific folder in the user's account.
![Dropbox App Image](https://drive.google.com/uc?id=1ct5DOppJgH5wR5bSJQIZeh6UiCsPLxPM)
2. Configure the Dropbox app settings with OAuth2 redirect URI, webhook URI, and App folder name.
    - Note: Redirect URI and webhook should be globally accessible, so use ngrok while running locally.
![Dropbox App settings](https://drive.google.com/uc?id=1ZVC546llUdFiyvX-LMewjMqmifAfApzM)
![Dropbox App settings](https://drive.google.com/uc?id=16kCxPaCBHMxwxkHlGD8UHFG5rTe_nlU0)
3. In Dropbox app permissions, select `account_info.read`, `files.metadata.read`, `files.content.read`, and click submit.
![Dropbox App permission](https://drive.google.com/uc?id=1ZYqs5eSikBdYPdnZLVMawTjMkguAxVuG)
4. Create `secret.json` in the Flask app folder to store details about your Dropbox app.
    - Example:
        ```json
        {
            "DROPBOX_APP_KEY": "3ms6sgw12m6jgw7",
            "DROPBOX_APP_SECRET": "m695hne8rnc45cm",
            "DROPBOX_redirect_uri": "https://9ceb-106-51-127-230.ngrok-free.app/auth"
        }
        ```
5. Create `cursor.json`, `refresh_token.json`, `access_token.json` to store user details.
6. Run the Flask app.

## Things need to know about Dropbox app:
1. Once the user allows our app, a folder for our app will be created in the user's account. The path of that folder is `Apps -> 'folder name we given in Dropbox'` (e.g., `docuedge` at `Apps/docuedge`).
2. If that folder in the same path as mentioned above already exists, it will use the same folder.
3. Dropbox provides us an encoded string called "cursor" used to track modifications. Store the user's cursor to track changes.
4. The user's access token obtained at the time of authorization is valid for 4 hours only. Regenerate the token with the refresh token, which has no expiry time. Store these data securely on the server.

## Flask app endpoints description:
1. `/home` endpoint:
    - Renders the welcome HTML page with an Authorization URL that takes the user to the Dropbox authorization page.
2. `/auth` endpoint:
    - Stores the user's access token and refresh token in JSON files.
    - Downloads existing files in Dropbox `Apps/docuedge` folder through `get_all_exist_files()`.
3. `/webhook` endpoint:
    - **GET method:** Used to enable the Flask app with the Dropbox app.
        - Receives an 'arg' param called 'challenge' and returns it with a 200 status code.
    - **POST method:** 
        - Receives JSON with a list of user IDs who made changes inside the folder created for our app.
        - Responds to these calls within 10 seconds, and further processes are done in threading in `process_update()`.
