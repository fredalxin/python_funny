import socket
from urllib.parse import urlparse,urlunparse

HOST='127.0.0.1'
PORT=33333

#接收客户端
def server(host,port):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((host,port))
    s.listen(500)
    print('Serving at:',port)
    while 1:
        try:
            conn,addr=s.accept()
            handle_connection(conn)
        except KeyboardInterrupt:
            print('Bye...')
            break

#处理连接逻辑
def handle_connection(conn):
    req_headers=get_header(conn)
    if req_headers is None:
        return
    method, version, scm, address, path, params, query, fragment=parse_header(req_headers)
    #将address去掉,仅保留路径而不是整个url进行转发
    path=urlunparse(('','',path,params,query,''))
    req_headers=' '.join([method,path,version])+'\r\n'+'\r\n'.join(req_headers.split('\r\n')[1:])
    soc=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    #请求服务器
    host=address[0]
    remote_ip=socket.gethostbyname(host)
    address=(remote_ip,address[1])
    try:
        soc.connect(address)
    except socket.error as arg:
        conn.close()
        soc.close()
    else:
        #连接成功,将Connection的keep-alive改为close
        if req_headers.find('Connection')>=0:
            req_headers=req_headers.replace('keep-alive','close')
        else:
            req_headers+='Connection:close\r\n'
        req_headers+='\r\n'
        #发送请求
        soc.sendall(req_headers.encode('utf-8'))
        print('send request...')
        print(req_headers)
        data=''
        while 1:
            try:
                buf=soc.recv(1024).decode('utf-8')
                data+=buf
            except:
                buf=None
            finally:
                if not buf:
                    soc.close()
                    break
        #转发给客户端
        print('receive request...')
        print(data)
        conn.sendall(data.encode('utf-8'))
        conn.close()


#获取连接头,筛去\r\n独立行
def get_header(conn):
    headers=''
    while 1:
        line=getline(conn)
        if line is None:
            break
        if line=='\r\n':
            break
        else:
            headers+=line
    return headers

#获取每一行
def getline(conn):
    line=''
    while 1:
        buf=conn.recv(1).decode('utf-8')
        if buf=='\r':
            line+=buf
            buf=conn.recv(1).decode('utf-8')
            if buf=='\n':
                line+=buf
                return line
        else:
            line+=buf

#处理连接头
def parse_header(headers):
    request_lines=headers.split('\r\n')
    first_line=request_lines[0].split(' ')
    method=first_line[0]
    full_path=first_line[1]
    version=first_line[2]
    print('%s%s'%(method,full_path))
    (scm,netloc,path,params,query,fragment)=urlparse(full_path,'http')
    #如果有端口用其端口,没有用80
    i=netloc.find(':')
    if i>0:
        address=netloc[:i],int(netloc[i+1:])
    else:
        address=netloc,80
    return method,version,scm,address,path,params,query,fragment

if __name__=='__main__':
    server(HOST,PORT)