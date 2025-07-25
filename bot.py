from aiohttp import ClientSession, ClientTimeout
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from eth_account import Account
from datetime import datetime
from colorama import Fore, Style
import asyncio, random, json, os, pytz, time

wib = pytz.timezone('Asia/Jakarta')
USER_AGENT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

class Sixpence:
    def __init__(self):
        self.BASE_API = "https://us-central1-openoracle-de73b.cloudfunctions.net/backend_apis/api/service"
        self.BASE_HEADERS = {}
        try:
            with open('refer.txt', 'r') as file:
                self.ref_code = file.read().strip()
                if not self.ref_code:
                    self.log(f"{Fore.RED}refer.txt is empty. Please add a referral code.{Style.RESET_ALL}")
                    raise ValueError("Empty referral code")
                self.log(f"{Fore.GREEN}Referral Code Loaded: {self.ref_code}{Style.RESET_ALL}")
        except FileNotFoundError:
            self.log(f"{Fore.RED}refer.txt file not found. Using default code: 3SO6MZ{Style.RESET_ALL}")
            self.ref_code = "3SO6MZ"
        except Exception as e:
            self.log(f"{Fore.RED}Failed to read refer.txt: {e}{Style.RESET_ALL}")
            self.ref_code = "3SO6MZ"
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.nonce = {}
        self.exp_time = {}

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}"
        )
        with open('log.txt', 'a') as f:
            f.write(f"[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ] | {message}\n")

    def generate_new_account(self):
        try:
            account = Account.create()
            private_key = account._private_key.hex()
            address = account.address
            return private_key, address
        except Exception as e:
            self.log(f"{Fore.RED}Failed to generate account: {e}{Style.RESET_ALL}")
            return None, None

    def save_account_to_file(self, private_key):
        try:
            with open('accounts.txt', 'a') as file:
                file.write(f"{private_key}\n")
            return True
        except Exception as e:
            self.log(f"{Fore.RED}Failed to save account to file: {e}{Style.RESET_ALL}")
            return False

    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            self.log(f"{Fore.GREEN}Proxies Total: {len(self.proxies)}{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED}Failed To Load Proxies: {e}{Style.RESET_ALL}")

    def get_next_proxy_for_account(self, email):
        if email not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = f"http://{self.proxies[self.proxy_index]}" if not self.proxies[self.proxy_index].startswith("http") else self.proxies[self.proxy_index]
            self.account_proxies[email] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[email]

    def generate_address(self, account):
        try:
            account = Account.from_key(account)
            return account.address
        except Exception:
            return None

    def mask_account(self, account):
        return account[:6] + '*' * 6 + account[-6:]

    def generate_payload(self, account, address):
        try:
            if address not in self.nonce:
                raise Exception(f"Nonce not found for address: {address}")
            issued_at = datetime.now(pytz.UTC).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            message = f"bcakokeeafaehcajfkajcpbdkfnoahlh wants you to sign in with your Ethereum account:\n{address}\n\nBy signing, you are proving you own this wallet and logging in. This does not initiate a transaction or cost any fees.\n\nURI: chrome-extension://bcakokeeafaehcajfkajcpbdkfnoahlh\nVersion: 1\nChain ID: 42000\nNonce: {self.nonce[address]}\nIssued At: {issued_at}"
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)
            return {"message": message, "signature": signature}
        except Exception as e:
            raise Exception(f"Generate Payload Failed: {str(e)}")

    def print_message(self, account, proxy, color, message):
        self.log(
            f"{Fore.CYAN}[ Account: {self.mask_account(account)} - Proxy: {proxy or 'None'} - Status: {color}{message}{Style.RESET_ALL}]"
        )

    async def get_nonce(self, address, proxy=None):
        url = f"{self.BASE_API}/{address}/nonce?"
        headers = self.BASE_HEADERS[address].copy()
        headers["Authorization"] = "Bearer null"
        headers["Content-Type"] = "application/json"
        async with ClientSession(timeout=ClientTimeout(total=60)) as session:
            async with session.get(url, headers=headers, proxy=proxy, ssl=False) as response:
                response.raise_for_status()
                return await response.json()

    async def user_login(self, account, address, proxy=None):
        url = f"{self.BASE_API}/login"
        data = json.dumps(self.generate_payload(account, address))
        headers = self.BASE_HEADERS[address].copy()
        headers["Authorization"] = "Bearer null"
        headers["Content-Length"] = str(len(data))
        headers["Content-Type"] = "application/json"
        async with ClientSession(timeout=ClientTimeout(total=60)) as session:
            async with session.post(url, headers=headers, data=data, proxy=proxy, ssl=False) as response:
                response.raise_for_status()
                return await response.json()

    async def bind_invite(self, address, proxy=None):
        url = f"{self.BASE_API}/inviteBind"
        data = json.dumps({"inviteCode": self.ref_code})
        headers = self.BASE_HEADERS[address].copy()
        headers["Authorization"] = f"Bearer {self.access_tokens[address]}"
        headers["Content-Length"] = str(len(data))
        headers["Content-Type"] = "application/json"
        async with ClientSession(timeout=ClientTimeout(total=60)) as session:
            async with session.post(url, headers=headers, data=data, proxy=proxy, ssl=False) as response:
                response.raise_for_status()
                return await response.json()

    async def process_user_login(self, account, address, use_proxy, retries=3):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        for attempt in range(1, retries + 1):
            try:
                nonce_data = await self.get_nonce(address, proxy)
                if nonce_data and nonce_data.get("msg") == "ok":
                    self.nonce[address] = nonce_data["data"]["nonce"]
                    self.exp_time[address] = nonce_data["data"]["expireTime"]
                    login = await self.user_login(account, address, proxy)
                    if login and login.get("msg") == "success":
                        self.access_tokens[address] = login["data"]["token"]
                        self.print_message(address, proxy, Fore.GREEN, "Login Success")
                        return True
                    else:
                        self.print_message(address, proxy, Fore.RED, f"Login Failed: {login}")
                else:
                    self.print_message(address, proxy, Fore.RED, f"Nonce Fetch Failed: {nonce_data}")
            except Exception as e:
                if "429" in str(e) and attempt < retries:
                    self.print_message(address, proxy, Fore.YELLOW, f"429 Too Many Requests, retrying {attempt}/{retries} after 15 seconds")
                    await asyncio.sleep(15)
                    continue
                self.print_message(address, proxy, Fore.RED, f"Error in Login: {str(e)}")
                break
        return False

    async def process_bind_invite(self, account, address, use_proxy):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        try:
            bind = await self.bind_invite(address, proxy)
            if bind and bind.get("success") is True and bind.get("msg") == "bind invite success":
                self.print_message(address, proxy, Fore.GREEN, f"Referral Code {self.ref_code} Bound Successfully")
            else:
                self.print_message(address, proxy, Fore.RED, f"Failed to Bind Referral Code: {bind}")
        except Exception as e:
            self.print_message(address, proxy, Fore.RED, f"Error in Bind: {str(e)}")

    async def main(self):
        try:
            num_accounts = int(input(f"{Fore.BLUE}How many accounts to create?: {Style.RESET_ALL}").strip())
            use_proxy = input(f"{Fore.BLUE}Use Proxy? [y/n]: {Style.RESET_ALL}").strip() == "y"

            if use_proxy:
                await self.load_proxies()

            self.log(f"{Fore.GREEN}Creating {num_accounts} Accounts...{Style.RESET_ALL}")

            accounts = []
            for i in range(num_accounts):
                private_key, address = self.generate_new_account()
                if private_key and address:
                    if self.save_account_to_file(private_key):
                        accounts.append(private_key)
                        self.log(f"{Fore.GREEN}Account {i+1} Created and Saved: {self.mask_account(address)}{Style.RESET_ALL}")
                    else:
                        self.log(f"{Fore.RED}Failed to Save Account {i+1}{Style.RESET_ALL}")
                else:
                    self.log(f"{Fore.RED}Failed to Create Account {i+1}{Style.RESET_ALL}")

            self.log(f"{Fore.GREEN}Total Accounts: {len(accounts)}{Style.RESET_ALL}")

            for idx, account in enumerate(accounts, start=1):
                try:
                    address = self.generate_address(account)
                    if not address:
                        self.log(f"{Fore.RED}[ Account: {idx} - Status: Invalid Private Key ]{Style.RESET_ALL}")
                        continue

                    user_agent = random.choice(USER_AGENT)
                    self.BASE_HEADERS[address] = {
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Origin": "chrome-extension://bcakokeeafaehcajfkajcpbdkfnoahlh",
                        "User-Agent": user_agent
                    }

                    if await self.process_user_login(account, address, use_proxy):
                        await self.process_bind_invite(account, address, use_proxy)
                    time.sleep(15)
                except Exception as e:
                    self.log(f"{Fore.RED}[ Account: {idx} - Error: {str(e)} ]{Style.RESET_ALL}")
                    continue

        except ValueError:
            self.log(f"{Fore.RED}Invalid input for number of accounts.{Style.RESET_ALL}")
        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Error.{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    bot = Sixpence()
    asyncio.run(bot.main())
