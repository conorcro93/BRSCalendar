from dateutil import parser
from datetime import timedelta
from selenium import webdriver

# Press the green button in the gutter to run the script.
class BRSAPI:

    def __init__(self, browser, driver):
        if browser == 'Edge':
            self.browser = webdriver.Edge(executable_path=driver)
        elif browser == 'Chrome':
            self.browser = webdriver.Chrome(executable_path=driver)

    def login(self, username, password):
        self.browser.get('https://members.brsgolf.com/killeen/login')

        # Get elements
        username_input = self.browser.find_element_by_id('login_form_username')
        password_input = self.browser.find_element_by_id('login_form_password')
        login_button = self.browser.find_element_by_id('login_form_login')

        # Login
        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()

    def get_booking_details(self):
        inc = 9

        self.browser.get('https://members.brsgolf.com/killeen/bookings')

        booking = self.browser.find_element_by_css_selector("main")
        booking_text_string = booking.text
        booking_text_list = booking_text_string.split('\n')

        booking_dates_raw = booking_text_list[0::inc]
        dates_booked = [parser.parse(x) for x in booking_dates_raw]

        holes_booked = booking_text_list[1::inc]
        round_times = [timedelta(hours=5) if '18' in x
                       else timedelta(hours=2, minutes=30)
                       for x in holes_booked]

        booking_description = ['\n'.join(booking_text_list[x:x+inc]) for x in range(0, len(booking_text_list), inc)]

        bookings = [{
            'start_datetime': x[0],
            'end_datetime': x[0] + x[1],
            'round_time': x[1],
            'description': x[2]}
            for x in zip(dates_booked, round_times, booking_description)]

        return bookings

    def quit(self):
        self.browser.quit()