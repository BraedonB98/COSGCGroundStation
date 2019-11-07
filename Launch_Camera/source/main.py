import pyautogui
import sys
import time
import subprocess

pyautogui.PAUSE = 1.5
pyautogui.FAILSAFE = True
username = 'admin'
correct_password = 'GndSt@tion'
ip_address = '128.138.75.76\n'

#add these constants to make it easier to change locations for pyautogui actions
url_click_x = 600
url_click_y = 230
# username_x = 
# username_y = 
# password_x = 
# password_y =
# login_x =
# login_y = 


def get_mousepos():
    while True:
        x, y = pyautogui.position()
        positionstr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
        print(positionstr)
        time.sleep(0.5)


def main():
    try:

        pass_counter = 3

        # Open Web Viewer
        subprocess.Popen('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe --profile-directory=Default --app-id=oddndbjhpcpopbebhonolceinkbnheih')
        # if pyautogui.locateOnScreen('src/web_viewer.png') is not None:
        #     pyautogui.doubleClick(pyautogui.locateCenterOnScreen('src/web_viewer.png'))
        # else:
        #     raise IOError

        # Select URL bar and fill camera url
        time.sleep(1.5)
        pyautogui.click(url_click_x, url_click_y)
        pyautogui.typewrite(ip_address)

        # If username dialog is already filled, then skip filling in username
        pyautogui.click(username_x, username_y)
        pyautogui.press(['delete', 'delete', 'delete', 'delete', 'delete', 'delete'])
        pyautogui.typewrite(username)

        # Prompt user for password
        # password = pyautogui.password(text='Enter password', title='Password', default='', mask='*')
        # while password is not correct_password:
        #     if password == correct_password:
        #         break
        #     pyautogui.alert(text=('Wrong Password Entered\nNumber of Tries Left: ' + str(pass_counter)), title='Error', button='OK')
        #     pass_counter -= 1
        #     password = pyautogui.password(text='Enter password', title='Password', default='', mask='*')
        #     if pass_counter == 0:
        #         pyautogui.alert(text='Out Of Tries\nTry Again Later', title='Error', button='OK')
        #         sys.exit()

        # Fill in password username
        pyautogui.click(password_x, password_y)
        pyautogui.typewrite(correct_password)

        # Click login button
        pyautogui.click(login_x, login_y)


    except KeyboardInterrupt:
        sys.exit()

    except IOError:
        pyautogui.alert(text='A Problem has Occurred', title='Error', button='OK')
        sys.exit()


if __name__ == "__main__":
    main()
    # get_mousepos()
