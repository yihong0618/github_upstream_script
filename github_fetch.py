import argparse
import re
import requests
from lxml import etree


class GitHub:
    def __init__(self, user_name, password, repo_name):
        self.headers = {
            "Referer": "https://github.com/login",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36",
            "Host": "github.com",
        }
        self.login_url = "https://github.com/login"
        self.post_url = "https://github.com/session"
        self.session = requests.Session()
        self.user_name = user_name
        self.pass_word = password
        self.repo_name = repo_name

    def token(self):
        response = self.session.get(self.login_url)
        html = response.text
        s = etree.HTML(html)
        t = s.xpath('//input[@name="authenticity_token"]')[0]
        token = t.attrib["value"]
        return token

    @staticmethod
    def _find_two_factor_code(text):
        t = re.findall(
            r'name="authenticity_token" value="(.*?)"', text, flags=re.DOTALL
        )
        if not t:
            raise Exception("Not find two factor token")
        return t[0]

    @staticmethod
    def _find_fetch_and_merge_code(text):
        t = re.findall(r'fetch_and_merge(.*)value="(.*?)"', text)
        if not t:
            raise Exception("Not find fetch and merge code")
        return t[0][1]

    def login(self):
        post_data = {
            "commit": "Sign in",
            "utf8": "✓",
            "authenticity_token": self.token(),
            "login": self.user_name,
            "password": self.pass_word,
        }
        res = self.session.post(self.post_url, data=post_data, headers=self.headers)
        res_text = res.text
        if res_text.find("two-factor"):
            two_factor_code = self._find_two_factor_code(res.text)
            print("please: enter your two-factor token\n")
            two_factor_token = input()
            data = {
                "utf8": "✓",
                "authenticity_token": two_factor_code,
                "otp": two_factor_token,
            }
            self.session.post("https://github.com/sessions/two-factor", data=data)

    def fetch_and_fork(self):
        self.login()
        r = self.session.get(f"https://github.com/{self.user_name}/{self.repo_name}")
        code = self._find_fetch_and_merge_code(r.text)
        data = {"authenticity_token": code}
        # fetch and merge real api
        res = self.session.post(
            f"https://github.com/{self.user_name}/{self.repo_name}/branches/fetch_and_merge/master",
            data=data,
        )
        if res.ok:
            print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user_name", help="github user name")
    parser.add_argument("password", help="github password")
    parser.add_argument("repo_name", help="repo you want fetch and sync")
    options = parser.parse_args()
    g = GitHub(options.user_name, options.password, options.repo_name)
    g.fetch_and_fork()
