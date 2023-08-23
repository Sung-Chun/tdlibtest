#
# Copyright Aliaksei Levin (levlam@telegram.org), Arseny Smirnov (arseny30@gmail.com),
# Pellegrino Prevete (pellegrinoprevete@gmail.com)  2014-2023
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
from ctypes.util import find_library
from ctypes import *
import json
import sys

log_message_callback_type = CFUNCTYPE(None, c_int, c_char_p)
# initialize TDLib log with desired parameters
@log_message_callback_type
def on_log_message_callback(verbosity_level, message):
    if verbosity_level == 0:
        sys.exit('TDLib fatal error: %r' % message)

class TdjsonApi:
    # For singleton (allow only one instance)
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):

        # load shared library
        tdjson_path = find_library('tdjson') or './libtdjson.so'
        if tdjson_path is None:
            sys.exit("Can't find 'tdjson' library")
        self.tdjson = CDLL(tdjson_path)

        # load TDLib functions from shared library
        self._func_td_create_client_id = self.tdjson.td_create_client_id
        self._func_td_create_client_id.restype = c_int
        self._func_td_create_client_id.argtypes = []

        self._func_td_receive = self.tdjson.td_receive
        self._func_td_receive.restype = c_char_p
        self._func_td_receive.argtypes = [c_double]

        self._func_td_send = self.tdjson.td_send
        self._func_td_send.restype = None
        self._func_td_send.argtypes = [c_int, c_char_p]

        self._func_td_execute = self.tdjson.td_execute
        self._func_td_execute.restype = c_char_p
        self._func_td_execute.argtypes = [c_char_p]

        _func_td_set_log_message_callback = self.tdjson.td_set_log_message_callback
        _func_td_set_log_message_callback.restype = None
        _func_td_set_log_message_callback.argtypes = [c_int, log_message_callback_type]

        _func_td_set_log_message_callback(2, on_log_message_callback)

        # setting TDLib log verbosity level to 1 (errors)
        print(str(self._td_execute({'@type': 'setLogVerbosityLevel', 'new_verbosity_level': 1, '@extra': 1.01234})).encode('utf-8'))

        # create client
        self.client_id = self._func_td_create_client_id()


    def _td_execute(self, query):
        query = json.dumps(query).encode('utf-8')
        result = self._func_td_execute(query)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    # simple wrappers for client usage
    def _td_send(self, query):
        query = json.dumps(query).encode('utf-8')
        self._func_td_send(self.client_id, query)

    def _td_receive(self):
        result = self._func_td_receive(1.0)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    def SetProxy(self):
        self._td_send({'@type': 'addProxy', 'server': '192.168.1.1', 'port': 8080, 'enable': True, 'type': {'@type': 'proxyTypeHttp'}})
        self._td_send({'@type': 'getProxies'})

    def DoAuthorization(self):
        # start the client by sending a request to it
        self._td_send({'@type': 'getOption', 'name': 'version', '@extra': 1.01234})

        # main events cycle
        while True:
            event = self._td_receive()
            if event:
                # process authorization states
                if event['@type'] == 'updateAuthorizationState':
                    auth_state = event['authorization_state']

                    # if client is closed, we need to destroy it and create new client
                    if auth_state['@type'] == 'authorizationStateClosed':
                        break
                    elif auth_state['@type'] == 'authorizationStateReady':
                        break


                    # set TDLib parameters
                    # you MUST obtain your own api_id and api_hash at https://my.telegram.org
                    # and use them in the setTdlibParameters call
                    if auth_state['@type'] == 'authorizationStateWaitTdlibParameters':
                        self._td_send({'@type': 'setTdlibParameters',
                                 'database_directory': 'tdlib',
                                 'use_message_database': True,
                                 'use_secret_chats': True,
                                 'api_id': 94575,
                                 'api_hash': 'a3406de8d171bb422bb6ddf3bbd800e2',
                                 'system_language_code': 'en',
                                 'device_model': 'Desktop',
                                 'application_version': '1.0',
                                 'enable_storage_optimizer': True})

                    # enter phone number to log in
                    if auth_state['@type'] == 'authorizationStateWaitPhoneNumber':
                        phone_or_token = input('전화번호 또는 봇 토큰을 입력하세요: ')
                        if len(phone_or_token) < 10:
                            print(f'잘못 입력하셨습니다.')
                            return False
                        elif len(phone_or_token) < 20:
                            self._td_send({'@type': 'setAuthenticationPhoneNumber', 'phone_number': phone_or_token})
                        else:
                            if phone_or_token[:3] == 'bot':
                                phone_or_token = phone_or_token[3:]
                            self._td_send({'@type': 'checkAuthenticationBotToken', 'token': phone_or_token})

                    # enter email address to log in
                    if auth_state['@type'] == 'authorizationStateWaitEmailAddress':
                        email_address = input('Please enter your email address: ')
                        self._td_send({'@type': 'setAuthenticationEmailAddress', 'email_address': email_address})

                    # wait for email authorization code
                    if auth_state['@type'] == 'authorizationStateWaitEmailCode':
                        code = input('Please enter the email authentication code you received: ')
                        self._td_send({'@type': 'checkAuthenticationEmailCode',
                                 'code': {'@type': 'emailAddressAuthenticationCode', 'code' : code}})

                    # wait for authorization code
                    if auth_state['@type'] == 'authorizationStateWaitCode':
                        code = input('Please enter the authentication code you received: ')
                        self._td_send({'@type': 'checkAuthenticationCode', 'code': code})

                    # wait for first and last name for new users
                    if auth_state['@type'] == 'authorizationStateWaitRegistration':
                        first_name = input('Please enter your first name: ')
                        last_name = input('Please enter your last name: ')
                        self._td_send({'@type': 'registerUser', 'first_name': first_name, 'last_name': last_name})

                    # wait for password if present
                    if auth_state['@type'] == 'authorizationStateWaitPassword':
                        password = input('Please enter your password: ')
                        self._td_send({'@type': 'checkAuthenticationPassword', 'password': password})

                    # handle an incoming update or an answer to a previously sent request
                    print(event)
                    sys.stdout.flush()

                # When error occurs, then return False
                if event['@type'] == 'error':
                    print(event)
                    sys.stdout.flush()
                    return False

        return True

    def GetChats(self):
        '''채팅방 ID와 제목 리스트를 획득한다.
        '''
        num_chats = 0
        chat_info_list = []
        print('\n☆☆☆☆☆   Sending getChats    ☆☆☆☆☆\n')
        self._td_send({'@type': 'getChats', 'chat_list': None, 'limit': 2})
        while True:
            event = self._td_receive()
            if event is None:
                break
            if event['@type'] == 'error':
                print('\n\n  ERROR  ===========')
                print(str(event).encode('utf-8'))
                print('                ---------------')
                return None
            if event['@type'] == 'updateNewChat':
                chat_title = event['chat']['title']
                chat_id = event['chat']['id']
                chat_info_list.append((chat_title, chat_id))
                print('----------------------------------------------------------------------')
                print(f'  ▶▶▶▶ 채팅방:  [{num_chats}] {chat_title},   (chat id: {chat_id})')
                sys.stdout.flush()
                num_chats += 1
            elif event['@type'] == 'updateChatLastMessage':
                chat_lastmessage_content = event['last_message']['content']
                if chat_lastmessage_content['@type'] == 'messageText':
                    message_text = event['last_message']['content']['text']['text']
                    print(f'    ⊙M⊙  LAST MESSAGE: [{message_text}]')
                elif chat_lastmessage_content['@type'] == 'messagePhoto':
                    message_photo_caption = event['last_message']['content']['caption']['text']
                    print(f'    ⊙P⊙  LAST PHOTO CAPTION : [{message_photo_caption}]')
                elif chat_lastmessage_content['@type'] == 'messageContactRegistered':
                    pass
                elif chat_lastmessage_content['@type'] == 'messageChatAddMembers':
                    pass
                elif chat_lastmessage_content['@type'] == 'messageSupergroupChatCreate':
                    pass
                else:
                    print(f'    ⊙ELSE⊙  Other : [{chat_lastmessage_content["@type"]}]')

        return chat_info_list

    def AddChatMember(self, chat_id, user_id, forward_limit=10):
        '''채팅방에 멤버를 초대한다.

        - chat_id: 채팅방 ID
        - user_id: 회원 ID
        - forward_limit: 초대한 회원에게 이전 메시지 몇개까지 보여줄 지 최대 100까지 설정
                        (Ignored for supergroups and channels, or if the added user is a bot)
        '''
        print('\n☆☆☆☆☆   Adding new member to the chat    ☆☆☆☆☆\n')
        self._td_send({'@type': 'addChatMember', 'chat_id': chat_id, 'user_id': user_id, 'forward_limit': forward_limit})
        while True:
            event = self._td_receive()
            if event is None:
                break
            if event['@type'] == 'error':
                print('\n\n  ERROR  ===========')
                print(event)
                print('    ---------------')
                return None

            print(event)


if __name__ == "__main__":
    tdjson = TdjsonApi()
#    tdjson.SetProxy()
    if tdjson.DoAuthorization() is True:
        print('\n☆☆ Authorization Done ☆☆')
        chat_info_list = tdjson.GetChats()
        if chat_info_list is not None:
            if len(chat_info_list) > 0:
                # 첫번째 방에 user_id=0인 회원을 초대한다. user_id=0인 회원은 없으므로 Error가 발생한다.
                tdjson.AddChatMember(chat_info_list[0][1], 0)
    pass
