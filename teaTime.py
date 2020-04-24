from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime, timedelta
import sys
import pandas as pd

import smtplib
from email.message import EmailMessage

from secrets import TT_email_user, TT_email_password
from secrets import TeeOn_username, TeeOn_password, user_email

# TODO - be able to book multiple tee times
# TODO - replace sleeps with waits from selenium


weekdays = {
    "monday":    "Monday",
    "mon":       "Monday",
    "m":         "Monday",
    "tuesday":   "Tuesday",
    "tues":      "Tuesday",
    "tue":       "Tuesday",
    "tu":        "Tuesday",
    "wednesday": "Wednesday",
    "wed":       "Wednesday",
    "w":         "Wednesday",
    "thursday":  "Thursday",
    "thurs":     "Thursday",
    "thur":      "Thursday",
    "thu":       "Thursday",
    "th":        "Thursday",
    "friday":    "Friday",
    "fri":       "Friday",
    "f":         "Friday",
    "saturday":  "Saturday",
    "sat":       "Saturday",
    "sa":        "Saturday",
    "sunday":    "Sunday",
    "sun":       "Sunday",
    "su":        "Sunday",
}

n_weekdays = {
    "Monday":    0,
    "Tuesday":   1,
    "Wednesday": 2,
    "Thursday":  3,
    "Friday":    4,
    "Saturday":  5,
    "Sunday":    6,
}


class TeaTime():
    def __init__(self):
        self.book_today = False

        self.driver  = webdriver.Chrome()
        self.WEBPAGE = 'https://www.tee-on.com/'
        self.driver.get(self.WEBPAGE)

        sleep(2) # give the page time to load

        self.login()

    def login(self):
        #driver.implicitly_wait(100)

        signInBtn = self.driver.find_element_by_xpath('//*[@id="sign-in-menu-btn"]')
        signInBtn.click()

        emailIn = self.driver.find_element_by_xpath('//*[@id="Username"]')
        emailIn.send_keys(TeeOn_username)

        passwordIn = self.driver.find_element_by_xpath('//*[@id="Password"]')
        passwordIn.send_keys(TeeOn_password)

        letsGo = self.driver.find_element_by_xpath('//*[@id="navbar"]/ul/li[6]/div/div[3]/a[2]')
        letsGo.click()

        sleep(2) # give the page time to go to sign in

        teeSheet = self.driver.find_element_by_xpath('//*[@id="scrollbar-wrapper"]/div[2]/a[3]')
        teeSheet.click()

        sleep(2) # Let the tee sheet load


    def reformatTeeDay(self, input_day):
        if input_day.lower() == 'today':
            input_day = datetime.today().strftime("%A")
            self.book_today = True
        else:
            if input_day.lower() not in weekdays:
                print('\n\tERROR: Weekday provided is invalid!\n')

        return weekdays[input_day.lower()]


    def reformatTeeTime(self, input_time):
        if ':' not in input_time:
            input_time += ':00'

        input_time = input_time.strip('am')
        input_time = input_time.strip('pm')
        input_time = input_time.strip(' ')

        # put time on 24 hour clock
        hour = int(input_time.split(":")[0])
        minute = int(input_time.split(":")[1])
        if hour < 7:
            hour += 12
            input_time = str(hour) + ':' + str(minute).zfill(2)

        return input_time


    def calculateTimeDiff(self, time1, time2):
        time1 = self.reformatTeeTime(time1)
        time2 = self.reformatTeeTime(time2)

        hour1 = int(time1.split(':')[0])
        hour2 = int(time2.split(':')[0])

        minute1 = int(time1.split(':')[1])
        minute2 = int(time2.split(':')[1])

        return (hour2-hour1)*60 + (minute2-minute1)


    def changeTeeSheetDate(self, tee_weekday, tee_time):
        # get today's date
        today   = datetime.today()
        n_today = today.weekday()

        n_teeDay = n_weekdays[tee_weekday]

        # If our days are the same, see if they want this week or next week
        daysToGo = 0
        if self.book_today:
            daysToGo = 0
        elif n_today == n_teeDay:
            # check to see if requested tee time is in the past
            if self.calculateTimeDiff(today.strftime("%H:%M"), tee_time) < 0:
                daysToGo = 7
            else:
                choice = input("\n\tIs this tee time for later today? [y/n] ").lower()
                if choice == 'y' or choice == 'yes':
                    daysToGo = 0
                else:
                    daysToGo = 7
        else:
            daysToGo = (n_teeDay - n_today + 7) % 7

        # Get delta from today to tee day and create tee day object
        td     = timedelta(days=daysToGo)
        teeDay = today + td

        # format the correct XPath for the correct date
        teeDate_XPath = '//*[@id="' + teeDay.strftime("%Y-%m-%d") + '"]'

        # navigate to the correct tee sheet date
        teeSheet = self.driver.find_element_by_xpath(teeDate_XPath)
        teeSheet.click()

        # save off the correct webpage
        self.teeSheetUrl = self.driver.current_url

        return 1

    def getOpenTeeTimes(self):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # parse out the tee times and players who may have it booked
        raw_times   = soup.find_all('td', class_='time')
        self.players = soup.find_all('td', class_='player-names')

        self.times  = []
        avail_times = []
        for i, dudes in enumerate(self.players):
            guys = dudes.text.strip('\n')
            guys = guys.strip('\xa0')

            tmpTime = raw_times[i].text.strip('\n')
            tmpTime = tmpTime.strip(' ')
            self.times.append(tmpTime)

            if guys == '':
                # add tee time with no guys signed up with no carriage returns and delete leading ' '
                tmpTime = raw_times[i].text.strip('\n')
                tmpTime = tmpTime.strip(' ')
                avail_times.append(tmpTime)

        return avail_times


    def chooseTeeTime(self, desired_time, open_times, num_times, threshold):
        good_times = pd.DataFrame(columns=['time', 'dt'])
        for time in open_times:
            dt = self.calculateTimeDiff(desired_time, time)

            # if the open tee time is within an hour of requested, track it
            if abs(dt) < threshold:
                good_times = good_times.append({'time': time, 'dt': dt}, ignore_index=True)

        self.tee_times = good_times

        # find tee times closest to desired input time by sorting abs(dt)
        sorted_idx = good_times['dt'].abs().argsort()
        if num_times == 1 and len(sorted_idx) > 0:
            return [good_times['time'][sorted_idx[0]]]
        else:
            return False


    def fillInTeeTime(self, chosen_time):
        for choice in chosen_time:
            idx = self.times.index(choice) + 1
            teeTime_XPath = '//*[@id="tee-sheet"]/tbody/tr[' + str(idx) + ']/td[1]/a'

            teeTime = self.driver.find_element_by_xpath(teeTime_XPath)
            teeTime.click()

            sleep(1)

            numPlayers = self.driver.find_element_by_xpath('//*[@id="details-players"]/div/div/label[1]')
            numPlayers.click()

            sleep(1)

            nextBtn = self.driver.find_element_by_xpath('//*[@id="details-next-btn"]')
            nextBtn.click()

            sleep(1)

            player1 = self.driver.find_element_by_xpath('//*[@id="Name1"]')
            player1.send_keys('Guest')

            player2 = self.driver.find_element_by_xpath('//*[@id="Name2"]')
            player2.send_keys('Guest')

            player3 = self.driver.find_element_by_xpath('//*[@id="Name3"]')
            player3.send_keys('Guest')

            bookBtn = self.driver.find_element_by_xpath('//*[@id="enter-players-wrapper"]/a[2]')
            bookBtn.click()

            continueBtn = self.driver.find_element_by_xpath('//*[@id="scrollbar-wrapper"]/table/tbody/tr/td[2]/a')
            continueBtn.click()

            # return back to tee sheet page
            self.driver.get(self.teeSheetUrl)

            sleep(1)


        pass


    def curateConfirmationMsg(self, day, times):
        msg = """<!DOCTYPE html><html><body>
                   <h1 style="color:#56b000;"> It's Tea Time!</h1>"""
        if len(times) == 1:
            msg += "<p>Congrats, you\'ve got a new tee time booked on "
        elif len(times) > 1:
            msg += "<p>Congrats, you\'ve got new tee times booked on "

        msg += "<b>" + day + " at " + ", ".join(times)

        msg +="</b></p></body></html>"

        return msg


    def curateFailureMsg(self, tee_day, tee_times, alternatives):
        msg = """<!DOCTYPE html><html><body>
                   <h1 style="color:#8a0303;"> No Tea For You!</h1>"""

        msg += "<p>Looks like all the old dudes already stole all the tee times on <b>"
        msg += tee_day + "</b> around <b>" + ", ".join(tee_times)
        msg += "</b>..."

        if len(alternatives) > 0:
            msg += "<p>Here's some other open tee times on " + str(tee_day) + " that you could book instead:</p>"
            msg += "<ul>"
            for time in alternatives:
                msg += "<li>" + str(time) + "</li>"
            msg += "<ul>"
        else:
            msg += "<p>Doesn't look like there any open tee times at all. Probably would've been a terrible round anyways...</p>"

        msg +="</body></html>"

        return msg


    def sendEmail(self, html_msg):
        msg = EmailMessage()
        msg['Subject'] = 'New Tea Time!'
        msg['From']    = TT_email_user
        msg['To']      = user_email

        # create plain style message if html is off
        msg.set_content('New Tea Time!')

        # create fancier HTML message
        msg.add_alternative(html_msg, subtype='html')


        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(TT_email_user, TT_email_password)
            smtp.send_message(msg)


    def bookTeeTime(self, tee_day, tee_time, num_tees):
        tee_day  = self.reformatTeeDay(tee_day)
        tee_time = self.reformatTeeTime(tee_time)
        num_tees = num_tees

        if num_tees > 3:
            print("\n\tERROR: Can only book up to 3 tee times!")
            return False

        if not self.changeTeeSheetDate(tee_day, tee_time):
            print("\n\tError Changing TimeSheet Date!\n")
            return False

        # get all available times for the day requested
        open_times = self.getOpenTeeTimes()

        # pick out an optimal time based on the tee time input
        self.picked_times = self.chooseTeeTime(tee_time, open_times, num_tees, 30)

        if not self.picked_times:
            print("\n\tERROR: Not a good time to pick!")
            return False

        emailMsg = []
        if len(self.picked_times) < num_tees:
            emailMsg = self.curateFailureMsg(tee_day, tee_time, num_tees, open_times)
        else:
            # loop through time(s) and book 'em
            print(self.picked_times)

            self.fillInTeeTime(self.picked_times)

            emailMsg = self.curateConfirmationMsg(tee_day, self.picked_times)

        # send confirmation email
        self.sendEmail(emailMsg)




if __name__ == "__main__":
    print('\n\tIt\'s Tea Time Baby!\n')

    # get when we want to book a tee time
    day    = input("\n\tWhich day do you wanna play? ")
    time   = input("\n\tAround what time do you want to play? ")
    #groups = int(input("\n\tHow many tee times are you looking for? "))
    groups = 1

    print("\n\tOk. Searching for %d tee times around %s on %s" % (groups, time, day))

    tea = TeaTime()

    tea.bookTeeTime(day, time, groups)
