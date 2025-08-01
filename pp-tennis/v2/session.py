import requests

class Session:
    LOGIN_URL = 'https://prospectpark.aptussoft.com/Member/Aptus/ClubLogin_LoginValidate'
    VERIFICATION_TOKEN = '4uFiKceNCUBTIM0SFwobhKwDPFe7ZecpJ8FP7scj_5x49iqQxIX0lYvhphxTg0pH8f6mpNvGbV_6snTTIcD1N_Wq-AHGVgJ2U8HIMhFo2iQ1:CVX49AzgU4Hh8MLtnc-rvwpQbXEJiCZvkZM9gJs763TviIQAOPLVrovSe0X6wWJPqjOGqWSU2d_OSvTl9haA-CzXiEBS992E8JIw4hu8PCk1'

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.login()

    def login(self):
        self.session.headers \
            .update({'requestverificationtoken': self.VERIFICATION_TOKEN})
        self.session.post(
            self.LOGIN_URL,
            json={
                'email': self.email,
                'pass': self.password,
            }
        )
