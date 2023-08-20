# tdlibtest

tdlib 테스트 프로그램

## Prerequisite

* TDlib 라이브러리 빌드 (https://github.com/tdlib/td) 한 뒤 tdjson.dll 파일을 PATH 환경변수 경로나 현재 경로에 복사한다.

아래와 같이 tdjson.dll 파일을 복사한다.
```
2023-08-20  오후 06:50    <DIR>          .
2023-08-20  오후 06:50    <DIR>          ..
2023-08-20  오후 07:44    <DIR>          .git
2023-08-20  오후 07:43             2,621 README.md
2023-08-20  오후 06:36    <DIR>          tdjson
2023-08-15  오전 12:14        64,592,384 tdjson.dll
```

## 실행 방법

아래와 같이 tdjson 폴더 아래의 TdjsonApi.py을 실행합니다.
```
python tdjson\TdjsonApi.py
```

## 구현 예제

**1. 인증 및 회원가입: DoAuthorization()**

최초 실행 시 DoAuthorization() 함수 내에서 폰 번호를 입력을 받고 인증번호를 입력을 받는다.
해당 폰 번호가 회원가입이 이미 완료 된 경우라면, 인증이 완료되고 다음 단계로 넘어간다.
회원가입이 안 된 경우라면, 이름 (first name, last name) 입력을 받고 회원가입이 진행이 된다.

if auth_state['@type'] == 'authorizationStateWaitTdlibParameters' 부분을 보면 setTdlibParameters를 설정하는 파라미터에 api_id와 api_hash는 my.telegram.org에서 발급받아서 설정하도록 한다.

**2. 채팅방 리스트: GetChats()**

인증이 완료된 후 GetChats() 함수로 (방 제목, 방 ID) 형식의 채팅 방 리스트를 얻어온다.
각 채팅 방의 마지막 메시지는 event['@type'] == 'updateChatLastMessage' 부분의 코드에서 얻어올 수 있다.

**3. 로그인 (봇으로 로그인 포함)**

회원가입이 된 회원의 경우, 최초 로그인은 위 1번 인증 과정에서 폰 번호와 인증번호를 입력하여 로그인이 완료되기 때문에 별도 구현을 하지 않았다.
최초 로그인을 하면 로그인 정보는 db에 저장이 되므로 다음 번 인증을 위한 DoAuthorization() 함수 호출 시 별도로 입력되는 절차는 없다.

봇 로그인은 폰 번호 대신 사전에 발급한 봇 토큰이 필요한데, 이 부분은 추가 예정이다.

**4. 프록시 설정: SetProxy()**

Proxy 서버는 http나 socks5 의 종류가 있는데, http proxy로만 테스트를 진행했다.
만약 socks5 proxy로 사용하여야 한다면, proxyTypeHttp를 proxyTypeSocks5으로 변경하면 된다.

**5. 그룹 / 채널 초대: AddChatMember(chat_id, user_id, forward_limit)**

사용자 1명을 채팅 방에 초대하는 함수를 구현하였으며, 채팅방 리스트의 맨 첫 번째 방에 user_id=0인 회원을 초대하도록 하였는데, user_id=0은 존재하지 않는 회원이므로 에러가 발생한다.
이것이 원하는 기능이 맞는지 확인을 해주시고, 수정이 필요하면 알려주세요.
