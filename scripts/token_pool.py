import json
import requests

class TokenPool:
    def __init__(self):
        self.tokens = [
            # PUT GITHUB TOKENS HERE
        ]
        self.token_queues = self.init_token_queue()

    def generate_headers(self, token):
        headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 \
                # (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                }
        return headers
    
    def init_token_queue(self):
        # (token, remaining number of queries)
        print("init queue")
        queue = []
        for token in self.tokens:
            headers = self.generate_headers(token)
            html_response = requests.get(url="https://api.github.com/rate_limit", headers=headers)
            html_response = json.loads(html_response.text)
            remaining = html_response["resources"]["core"]["remaining"]
            queue.append([token, remaining])
            print(token, remaining)
        return queue


    def get_next_token(self):
        # always use first token
        # keep rotating if first token has no remaining
        while self.token_queues[0][1] == 0:
            self.token_queues.append(self.token_queues.pop(0))
        
        # finish finding a token with non-zero remaining
        print("using token", self.token_queues[0])
        headers = self.generate_headers(self.token_queues[0][0])
        # update token count
        self.token_queues[0][1] -= 1

        return headers
    

    def check_limits(self):
        for t in self.tokens:
            headers = self.generate_headers(t)
            html_response = requests.get(url="https://api.github.com/rate_limit", headers=headers)
            html_response = json.loads(html_response.text)
            print(html_response["resources"]["core"])
        pass