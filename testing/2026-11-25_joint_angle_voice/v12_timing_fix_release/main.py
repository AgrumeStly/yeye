# 直角＋钝角联合弯 v12，等待本地 Go。
GO_RECEIVED_PCM = (
    b'\xfe\xff\xfd\xff\xfe\xff\xfc\xff\xfe\xff\xfe\xff\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xff\x00\x00\x01\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\xff\xff\x01\x00\x01\x00\x00\x00\x00\x00\xfe\xff'
    b'\x00\x00\x00\x00\xff\xff\x01\x00\x00\x00\x02\x00\x02\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\xff\xff\x00\x00\xff\xff\xff\xff\xfe\xff\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x02\x00\x00\x00\x01\x00\x00\x00\xff\xff\x00\x00\x00\x00\xff\xff\x01\x00\xfe\xff\xff\xff\xff\xff\xff\xff\x00\x00'
    b'\x00\x00\x00\x00\x00\x00\xff\xff\xfd\xff\xfe\xff\xfe\xff\xfd\xff\xfe\xff\xff\xff\x00\x00\xfe\xff\x00\x00\x01\x00\xfe\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00\x01\x00\x00\x00\x00\x00\x01\x00\xff\xff\x00\x00\xff\xff\x00\x00\x00\x00\xfe\xff\xff\xff\x00\x00\xff\xff'
    b'\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\x01\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x01\x00\x00\x00\xff\xff\x00\x00\xff\xff\x00\x00\x00\x00\xfe\xff'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x01\x00\xff\xff\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x02\x00\x02\x00\x00\x00\x01\x00\x01\x00\x01\x00\x00\x00\xff\xff\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\xfe\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\xff\x00\x00\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x02\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x02\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\xff\xff'
    b'\xff\xff\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x00\xff\xff\xfe\xff\x00\x00\x01\x00\x02\x00\x01\x00\x01\x00\x01\x00\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x01\x00\x00\x00\x03\x00\x01\x00\x02\x00\x02\x00'
    b'\x01\x00\x01\x00\x02\x00\x01\x00\x01\x00\x00\x00\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x04\x00\x04\x00\x01\x00\xfd\xff\xfb\xff\xfd\xff\xff\xff\x02\x00\x04\x00\x03\x00\x03\x00\xfe\xff\xfa\xff\xff\xff\x04\x00\x06\x00\x01\x00\xff\xff\x00\x00\x00\x00\x06\x00\t\x00\x00\x00\xf9\xff'
    b'\xfc\xff\xfd\xff\x07\x00\x18\x00\x12\x00\x03\x00\xf5\xff\xf6\xff\x11\x00\x12\x00\xfb\xff\xef\xff\xed\xff\x07\x00\x18\x00\t\x00\x03\x00\xf1\xff\xee\xff\xf7\xff\t\x00"\x00\x07\x00\r\x00\x0e\x00\xf4\xff\x01\x00\xfd\xff\x07\x00+\x00\x06\x00\xe7\xff\xfe\xff\xd8\xff\xd3\xff\x1e\x00\x17\x00\xfd\xff\n\x00\xf2\xff'
    b'\xe6\xff\x12\x00*\x003\x00\x17\x00\xba\xff\xb8\xff\xf5\xff\x07\x004\x00&\x00\x0c\x00\x16\x00\xdb\xff\xb4\xff\xed\xff>\x00?\x00\xff\xff\xe6\xff\xe9\xff\xf0\xff4\x00F\x00\xe3\xff\xba\xff\xe3\xff\xf0\xff\x0c\x00A\x00\x0f\x00\xec\xff\xed\xff\xc7\xff\xec\xff\x00\x00\x13\x00H\x00\x05\x00\xd6\xff'
    b"\x0c\x00\x08\x00\xe8\xff\xfc\xff*\x00\xe3\xff\xb8\xffi\x00W\x00t\xff\x9c\xff\xf9\xff\xfc\xff_\x00j\x00\xf6\xff\xda\xff\xf2\xff\x91\xff\xba\xffw\x00g\x00I\x00(\x00\xa8\xff\x9b\xff\xee\xff\xe9\xff\xe1\xffT\x00h\x00\x18\x00\xf5\xffx\xffn\xff'\x00j\x00X\x00\xcb\xff`\xff"
    b'&\x00H\x00\xdf\xff_\x00Y\x00b\xff\xaf\xffu\x00\xe8\xff\xef\xff\x82\x00M\x00\xe2\xff\xa4\xff\xe4\xff\x0b\x005\x00d\x00\xff\xff$\x00\x0e\x00v\xff\xd1\xff\x0b\x00\x04\x004\x00\xfa\xff\xf1\xff#\x00\xf2\xff\xcc\xff\xe4\xff\xac\xff9\x00v\x00\xe1\xffo\x00\x13\x00>\xff\xc9\xff'
    b'Y\x00\x80\x00\xe0\xff\x93\xff0\x00\x8e\xff\x94\xff"\x01E\x00\x8e\xff\xe1\xff&\xff\x05\x00H\x00\x1a\x00\x1c\x01\xe9\xff\x1f\xffk\x00\xf7\xff\xd7\xff}\x00\xe7\xfe\x10\x00\xd4\x01\xaf\xff\xf5\xfen\xff\xae\xffl\x00\xdb\x00\x9e\x00M\xff\xdf\xfe\x03\x00\xa8\x00\xde\xff\x89\xff\xa4\x00\n\x01'
    b'w\xff\x03\xff\xef\xff)\xffT\x00\xe7\x01\xc6\xffo\xff_\x00\xa1\xff\x18\x00#\x00R\xff<\x00\x91\x00\xee\xff\xaa\xff)\xfft\xffP\x00\xfc\x00\xbc\x00\xbd\xff\x1a\xffM\xff\x85\x00\xb7\x00\xd7\xffi\xff\xa0\xff\xbf\xff$\x00\xf0\x00\xf3\xff\xc9\xffI\x00\xef\xfe\xf1\xff\x19\x01*\x00'
    b'!\x00\x96\xff\xef\xff:\x00 \xff\xdb\x00Q\x00/\xffv\x003\xff%\x00"\x00\x18\xff\xac\x013\x00@\xfe\xfc\xff\n\x00\x0e\x003\x01i\x00j\xff2\xff\xd6\xfe@\x00p\x016\x01\xa1\x00\xa3\xfe\x13\xfe\xaf\xff*\x00#\x01\xb5\x01\x90\xff\x9a\xfe\xc5\xff\xf6\xffE\x00\xfe\x00'
    b"M\x00\x95\xff;\xff\x87\xff~\x00V\x00\xca\x00\x05\x01H\xfe\x83\xfd\x1f\x01\x88\x02\xe5\x00\xd9\xff_\xfeg\xfe\xf9\x00O\x01\xa1\xff\xb0\xff\xe9\xffP\x00S\x00K\xff\xee\xff\xfa\xff?\x00r\x00\xc5\xff'\x00\x89\xff\xdf\x00\xd1\x00\xcd\xfe\x16\x00t\xff\xfa\xff6\x02\x9d\xffw\xfe"
    b'_\x00\xac\xfe\xcf\xff\x92\x02|\xfe\xeb\xfe\xba\x02\xf5\xfe\xe3\xfd\x1c\x02\xc2\x00t\xfd\x9f\x008\x02\x8c\xfe\x0c\xff\xcb\x01\xe8\x00\xfd\xfe\xce\xfe\x9e\x00{\x00\xc9\xffA\x01\xea\xff\xd9\xff\xe4\xff\xb6\xfdD\x00\x9e\x019\x00\xbd\xffl\xff\x15\x00\n\x00\xf4\xff\xd2\xff\x88\xff>\xff\x1d\x02'
    b'\xea\x00~\xfdB\x02\xd9\xff\x8c\xfcb\x01\x15\x02\xf2\x00\xd2\xff\xb7\xfe\xc2\xfe\x80\xff\xf1\x00T\x00L\xff\xa1\x00\x9c\x00\xec\x00\xd4\x00\xae\xfd6\xfe\x03\x00\n\x01\x01\x01\x02\x01\xa0\x00I\xfe?\xff\xd6\xff\x97\x00\xa9\xff<\x00\x0f\x03`\xfe*\xfe\xd2\xffq\xfe\xdd\x01\xc0\x02!\x00'
    b'\x99\xfd\x17\xfe\xda\x00\xa9\x00\x9a\x00\x14\x01\xf8\xfeJ\xff\xa9\xff@\xffF\x01K\x01;\x00\xbb\xfe\xf4\xff\xd7\xff\xaa\xfe\xa3\x02\xb9\x01[\xfe\x93\xfdl\x00\xec\x01\xbd\xfeC\x01r\x00\xa6\xfd\x84\x00t\x00\r\x00\x0c\x00\x0b\x01\x90\x00^\xfd\xa5\x00\xf5\x00\x9b\xfc\x18\x02\x1b\x05e\xfd'
    b'\xff\xfbJ\x01\xf2\x00[\xff\x85\x01\xe5\x00w\xff\xa0\xffG\x00j\x00\xa3\xfc\t\x00}\x03\xb2\xfe-\x021\x01\xe3\xfc\xc1\xffC\xfe\xbe\x00\xa4\x03\x94\x00\t\x00\xc7\xfe\xae\xfc\x0c\xff\xc4\x01\xb4\x01\xf7\x02W\xfe\xe2\xfa\xbf\x01\xb5\x00"\xff8\x03S\xff\t\xff\n\x01\xd7\xfd\xf7\xfe'
    b'\xf3\x02\xeb\x01\xa8\xfc\xc2\xfe\xdc\x03\x0f\x00b\x00`\x001\xfb\xa5\x00\x1c\x04)\x00\x02\x01\xc7\xff9\xfb\x8d\xfe\xbf\x02\x10\x01\xe4\x02\xcb\xfdO\xfb\x0c\x04f\xfe\xe6\xfd\x1c\x05\x81\xfe\xf2\xffo\x02\x81\xfbk\xfds\x05\xb0\x02\xbe\xfcc\xfe\x0f\xffX\x02\x03\x02\x9e\xff\xf3\xff|\xfb'
    b'b\x00t\x03\x00\x00\xc7\x00h\xfdS\xfe:\x00\xb6\x02k\x04\xc5\xfb\xbc\xfd\x7f\x01\x03\xff\x10\x03x\xff\xc9\xfe[\x02h\xff\x0e\x00e\xfd\x91\xfe\x03\x03\xf4\x01\xda\x00\x8a\xfd\xd3\xfe\xa0\xfes\xffT\x05\xa6\xffv\xfc\xc5\x00\x8b\x00W\xff\x99\xff\xe3\x00\x8f\xffX\x00\xa3\x00\x98\xff'
    b"N\xff\xdd\xfc\x7f\x02\x85\x03\n\xfcK\x00\x82\x03)\xfdH\xfd\xfd\x02\xea\x001\xfdn\x02\xd1\xfe\xcd\xfdD\x07t\xfc\x8d\xfbZ\x06\x80\xfci\xfc`\x06\xd7\xffe\xf9n\x02\xcd\x01\xaa\xfe\x82\x03\xd6\xfd\xbc\x01'\x00%\xf8\x90\x04\x9f\x03\xae\xfd\xf9\x028\xfc\xad\xfd\x1f\x06G\xfe"
    b'\xa9\xfc\n\x02\xf2\xff\xdb\xfe<\x01V\x00H\xfe4\x02+\x00u\xfe\xe4\x01\x14\xfd\xa5\xfe\xa1\x03}\x00R\xfe\xa9\xff|\x01\x9f\x00V\xff\xd3\xfd\xcc\xfd%\x03\x1a\x03\x83\xfe#\x00\x04\xfdY\xff\xad\x06\xac\xfbQ\xfcc\x05$\xfe-\xff>\x02\x8e\xfd\xac\xff\x99\x02 \xffF\x00'
    b'\xc7\x01\xd1\xfcc\xfe\x12\x03\x0e\x03\xd6\xfdZ\xfb\xdf\x02\xdb\x04\x14\xfda\xfb\xac\x02$\x02\x01\xfe\xc2\x02z\xff\xb8\xfa\x19\x02\x1b\x02X\xfe%\x02P\x00A\xfef\x01m\xfeS\xfd^\x006\x02\x96\x049\xfd\xfc\xf9\xe1\x02\xae\x01\xe2\xfeS\x02\x05\x00]\xfek\xfe`\xfd\xf5\x03'
    b'\xa9\x03\x8f\xfd_\x00\x0c\xfeG\xfd\xb9\x04\x95\x00\x88\xff6\x01\xbe\xfa\xac\x02\x88\x02\xa3\xfe\xc2\x01\x99\xfa&\x03`\x03\xdf\xf8S\x02)\x03\x9c\xfe\xf5\x02\x90\xfd6\xf9\xbc\x06/\x03\xca\xf7y\x04\xf0\x04\x0c\xfb\x89\xfdm\x02N\x03@\xfcx\xfe\xc8\x05c\xff\xb7\xfaE\xfe\xcb\x04'
    b's\x02!\xfc\xbe\x01\x0b\xfe\x85\xfe>\x04&\xfc\x17\x02]\x05\xb1\xf9\xe3\xfab\x05]\x02\xed\xfc\x85\x02\x93\xff\xa9\xff\xc6\xff\xfb\xfb\t\x02\xef\x01L\x01\xe6\x01J\xfd1\xff(\xfe\x05\xfd\x8e\x07\x0c\x03j\xfa\x91\xfd\xb1\x016\x04&\xfe\x8f\xfe.\xfd\xd9\x01\x1f\x07\x08\xf8\xf4\x00'
    b'\xf5\x03/\xfc\x19\x05%\xf9\xa6\xfd\xdd\n\xae\xf9\x11\xfe\x91\x05l\xfal\xff\x19\x02f\x00\x17\x05\xd6\xfe\xcd\xf8\x95\x01\xa1\x03g\xfd\x1d\x03Q\xffJ\xffa\x05k\xf7\xb5\xfeB\x05u\xfd\xff\x01\x8e\x00\xfa\x01\xeb\xfd/\xfcB\x01\xa2\x01\x17\x03$\xfb\xf6\xff \x06\x0b\xfb<\xfe'
    b'\x7f\x00D\xff\xb7\x05\xa1\x00\xfa\xfa\x84\xff\xa0\x03\xa8\xfc\x07\xfe|\x08\x9c\xfe\xa5\xfa\x14\x00\xf0\x02\xc4\x01\xd6\xf8\xe4\x03\x89\x04?\xfb\x90\x01\xab\xfdr\xffj\x02\xef\x02\t\xff2\xf94\x07(\xff\x83\xf5Y\n\xa5\x07\xa1\xf4\x84\xfc\xac\x08\x95\xfe\xf4\xfa\xad\x02\x01\x03\x9f\xff\xd5\xfb'
    b'\x8c\xffm\x05T\xfd\x02\xfey\x04A\xfd\x7f\x00\xa2\xfe\r\x00H\x063\xfa\xf0\x01\xa8\x01^\xfb\xad\x04{\xfd\xaf\x00w\x03\xcd\xfa\xfc\x00y\x028\xf8\x98\x02D\n"\xf7g\xfd\xf3\x07\x91\xfa<\xfeA\x06\x9b\x01=\xfe\x06\xfc\xd0\xfbC\x05\x96\x03\x9c\xf9\xea\x03#\x03\x96\xfc'
    b'h\x01\x93\xf9\xb0\xfe\xb1\x0b\x07\x01\xd7\xf7\xa9\xfd\xb0\x03Y\x01\x8e\xfd\xb3\x045\x01c\xf7\xbd\x00\x81\x05\xdd\xfcT\xfeN\x06\xf3\xfc\xde\xfd\xe7\x02_\xf8\x04\x04N\x04!\xff\x16\x04\xee\xf5\xac\xff\x0f\x0b\xa2\xfa8\xfeE\x03\xcd\xf84\x07`\x06\x0e\xf2\xbd\x00+\x06\x84\xfc\x0f\x03'
    b'\x14\x04\xbf\xf9\xe5\xfa\x8e\x04\xc1\x01`\xfd.\xfe\x00\x03\t\x04V\xff\xd7\xfb*\xfbs\x01\n\to\x03\xe8\xf9\xf7\xfb\xcb\xfe\xda\x04\x90\x02\x12\x00+\xff,\xf9\xfa\x07Z\x00\x1e\xf6\x05\x06\x16\x01\x95\xff\xdc\x06=\xfa\x80\xf4Y\nY\x05\xfe\xf5\xec\x06\xef\x01\x9d\xf8"\x02_\x03'
    b'^\x00\x07\xfb\xa4\x00\t\x08C\xfe\xca\xf7\x16\xffo\x06\xd6\x00\x8a\xfd\xfb\x02I\xfa\x96\xff\xe4\x05\xaf\xfa\xa7\x04\xa6\x02\xce\xf7(\x00\xa3\x04\xd6\xfd\xa3\xfd\x15\x05\xd2\xfe[\x01\xae\xfe\x9b\xf8\xd2\x04\x92\x02\x1e\x01\xf7\x011\xfcC\x00\xb4\xfd\xac\xfc.\t\x88\x010\xf9\x9e\x03\x12\xff'
    b'\xa8\xfdA\x02\xb1\xfc\x08\x00\x1d\x04\xcf\xffm\xff5\xfb>\xfd]\ng\xff?\xf9\x0f\x02%\x02Z\x008\xfb6\x03\xcc\x02\xb4\xfd \xfeB\x00\x9d\x048\xf9\xde\x01\xd0\x04\xa7\xfa\x16\x04\x1f\xfc,\xfe#\x08i\xfc3\xfc\x02\x03J\x03\xe9\xfd\x16\xfc\x0f\x04<\x01\xfe\xfe8\x01'
    b'\xf7\xfc\x10\x02F\x00\x8f\xfd\x08\x01\xf8\xffo\x05K\xfa/\xf8\xab\re\x00\x8c\xf2U\x070\x06\x1d\xf5G\x04-\x03\x94\xf5\xa5\x0b5\x04{\xf7f\x01B\xfb\t\x05\xd7\x01\xe9\xfa0\x07\xe4\xfbQ\xfb\xa7\x01a\x01R\x06P\xf8f\xfc\x9f\x0b\x08\xfcR\xf6\x16\x05\xce\x08\xe0\xfc'
    b'F\xf8\xc1\x016\x02\x9b\xfb\x92\x00\x87\x07\xe9\xfd\xaa\xfc\xd5\x02\xb8\xf9\xb0\x002\t-\xfd"\x00\xa8\xff\xce\xfa{\x04\xe0\xfe\xb2\x01P\x05v\xf9\x15\x00p\x01M\xfbP\x02\xf2\x03\xdc\xfdH\x03\x0e\xfe;\xf5\xd9\t\xf2\x02\x9b\xf5\x07\t\xba\x02\xf4\xf7W\x00\x80\x03k\x00\r\xfd'
    b'}\x02\xb9\x01\xe0\xfd$\x00\t\xfeD\x02Z\x00\xf7\xfc\xaf\x02z\xfd_\x00\xb5\x02\xe9\xfb\x19\x035\x01\x9c\xfb\n\x02\x0e\x02\xb7\xfe\xe0\x00_\x00\x04\xfd1\x01\xe5\x02\xfd\xff\x98\xfc\xc9\xfc\xcd\x06]\x01z\xfb\xc6\x03C\xfev\xff\xd4\x04!\xfc\xd2\xfc`\x02*\x01x\x02\xce\xfe'
    b'\x83\xfb2\xfd\x9f\xfa\xc3\x04\x99\x03\xee\xfc\x95\x02B\xfd\x8d\x03\xa6\xfeJ\xf7`\x07\x07\x04\xba\x01\xa7\x03\xf9\xf5\x10\xfe\xed\x07\x1b\xfcu\x02\x9b\x03\xb2\xf8\xfe\x00\x06\x01z\xfc\xd3\x02\xd7\x01\x93\xfd~\x03^\x02R\xf7\x95\xfc\xc4\x04\xad\x02\x9e\x01\xf6\xfe\xd5\xfd\xa5\x01d\xfe)\xfc'
    b'6\x01O\x02\x87\x02.\x00K\x01u\xfd\xcd\xfcY\x05`\xfb\xa5\x01\x00\t\xe6\xf7\xcf\xfe\xb9\x01\x16\xfb\x89\x02\xae\xfe\xda\xfer\x07\\\x00\xad\xfa\xa6\xff\x83\xfe4\x00\xdc\x06Y\xff9\xff\x83\x05\x80\xf8J\xfd\xa4\x03\r\xfb\x11\x03v\x03Z\x01\xa9\x00&\xfb\x05\xfc\xa0\x00\xc2\x05'
    b'V\xff\x99\x00v\x02u\xfa\xec\xfea\x00P\xfc\xbb\x01\xc3\x06\xd8\xfew\xfbW\x01\x8f\xfcl\xfc\xfb\x05\xbd\xfe\x86\xff\x94\x07&\xfa\x81\xfe]\x04\x8a\xfa\x86\xfe\xe3\x05\xa8\x01\xc3\xf9=\x01\xd9\xfd\x81\xfc\x94\x05X\xfe\xbb\x04\xc1\x00\x9b\xf7~\x03\xc6\x00\xaf\xfe\xbd\x04D\xfee\xfe'
    b'\xf9\x04\x05\xfe"\xfb\xb8\x00`\x00\x9c\xffN\x03w\xff\x87\xfcw\x02L\xfe*\x00P\x04F\xfc\x11\xfd\xbe\x01\x1c\x01\xc5\xff\xf0\x00\x0e\x00\x9c\x00\xcd\x00\x8c\xfb \xfd\x02\x02\xc8\x02\x9a\x01\xa2\x03\xeb\xfd8\xfb?\x03\x13\xfcJ\xff2\t\xf5\xfd\x1c\xfe\xfd\x00\xbc\xf9\x03\xff\xe3\x00'
    b'\xcf\xfe\xcf\x03\x8e\x01j\xfe5\xfeQ\xfe\x18\xff\x1d\xff\xc1\x01K\x03\xae\x01!\xff\x9e\xfd\x93\xfd~\xfeB\x00/\x02\xa8\x03\xfb\x00\x00\x00\x12\x00j\xfd\xd9\xff2\x00\xeb\xfe\xbe\x04\xcd\x03\xa6\xfd$\x00S\x00\t\xfe\xb1\xffm\x01&\x02*\x01}\x019\x00V\xfe\x10\xfe \xfe'
    b'\xa6\xff\xa8\x00\x1c\x02P\x02\xfa\x00\xfb\xfdh\xfc\n\xfd\xae\xfdg\x02\x06\x02i\xffb\x01\x93\xfe\xbc\xfb\xd9\xfd\xb5\xff\xbd\x01\x14\x02b\x01\t\x01\xf8\xfe\x01\xff\xcc\xfeE\xfe\xcd\x00G\x03\x89\x01\x00\x00\x8c\x01\xf3\xfdW\xfdV\x00=\xff\x87\x00\x9b\x01G\x01/\xff\x95\xfe\x9c\x00'
    b'K\xff\xea\xff\x1a\x01\x8a\x00\xe5\x00q\x00\x1f\x00\xaa\xff(\xffO\x00s\x00\xbb\xff-\x00;\x00\xd8\xff\x9f\xffI\x00o\xff\xed\xfe}\x00"\x01\x18\x04Z\x05\xc7\x038\x028\x00E\x00\xa8\x008\x02\x02\x04\xcd\x03\x92\x02)\x00\x96\xfe\xc1\xfd\xf8\xfdl\x00\x08\x02\xd7\x01"\x01'
    b'\xa1\xff\xe8\xfd\x02\xfdA\xfe\xba\xff\x7f\x00\x84\x010\x00\x8c\xfe\x80\xfd\xea\xfc\xa7\xfdP\xfe\x01\x00K\x00+\xff\xe4\xfeI\xfew\xfd\xc1\xfd\xf3\xff\xb9\x009\x00\x99\x00\x1c\x00N\xff3\xff\xbc\xff|\x00\xcd\x00i\x01r\x01:\x008\x00r\x00\x13\x00\xd3\x00P\x01\xa7\x01v\x01'
    b'\x97\x00\xb6\xff`\xfe\xb8\xfe?\x03r\t\xb1\x0c\xc5\r\x14\r+\n\x16\x07\r\x05\xa2\x04\xeb\x04\xd3\x05\xd2\x06\xd1\x05"\x03\xda\xff\x1b\xfc\xd5\xf9\x89\xf9\xf6\xf9N\xfbq\xfd3\xff\x90\xfe\x99\xfc\xfc\xfa\x1c\xfag\xfa\x99\xfb\xa3\xfd\xec\xfeu\xff\x08\xffA\xfdS\xfb\xe7\xf9\xfd\xf9'
    b"q\xfbV\xfd\x8d\xfeE\xff\x95\xffy\xff\xc6\xfe'\xfe\xd5\xfe\x9d\x00\x17\x03l\x04\x0b\x05>\x05-\x04\x1b\x03\xa9\x02\x81\x02\x92\x02K\x03:\x04\xc0\x04\xc7\x03\xd3\x01\xa4\x00\xeb\xff\xc8\x007\x05?\x0b\xb7\x0e\x9c\x0f0\x0e\xa9\n3\x07\xe9\x04\x1a\x04s\x04\xe4\x05\x18\x06\xdd\x03"
    b'\x1d\x01Q\xfdG\xf8\xa7\xf4\xb1\xf3\x96\xf4I\xf6\xe0\xf8\xe7\xfb\xeb\xfc\xf0\xfb\x94\xfa\x7f\xf9r\xf8+\xf93\xfcx\xfeK\x00\xa2\x01\x8b\x01\xce\xffd\xfd\x92\xfc`\xfc\x1a\xfdJ\xff\x9d\x01\x8a\x03\r\x05*\x05\xb2\x03\xd2\x02\x07\x03\x88\x03\x89\x040\x06b\x07\xad\x07\x10\x07\x8a\x05'
    b'\\\x03\x05\x01\xa1\xfft\xff\x10\x00W\x00\x1a\x00\xa5\xff\xd2\xfe\x82\xfet\x02\x88\n\xec\x10Z\x14\x15\x15\xcb\x12.\x0e\x9d\x08\xc3\x03T\xff5\xfdc\xfe\x92\xff\xcd\xfe\xd1\xfch\xf9\xff\xf4\x8a\xf1\xe8\xef7\xf0*\xf3U\xf8&\xfd3\x00$\x01I\x00K\xfei\xfc\x19\xfcb\xfc'
    b'\x9e\xfd\xd6\x00/\x04\xa9\x04\xf1\x02q\x01\x88\xff5\xfd-\xfc\x12\xfda\xff\xe2\x02p\x06:\x08\xf7\x07\x17\x07\xad\x05\xad\x03\x85\x02\x14\x02\x88\x02\x91\x03\xcd\x04\x0c\x05\xfb\x02y\x00(\xfe/\xfc\xba\xfa\xd2\xf9\xf7\xf9u\xfb\xbc\xfe\xb3\x05\xd3\x0f\x12\x17\xdf\x19F\x1b;\x1a$\x14'
    b'\x88\x0c\xc3\x06\x06\x01z\xfc\xcf\xfb\xed\xfc3\xfc\x0f\xfa\xc2\xf7\xa7\xf4\x03\xf18\xee\xc2\xec{\xee/\xf4S\xfa\x96\xfe\xad\x01P\x04\xa9\x04h\x02\xea\xff\t\xfe\xd1\xfcc\xfd\x00\x00\x91\x01\x05\x01\xe0\x00\xd7\x00\x0e\xff\x15\xfd\x91\xfcs\xfd\xc8\xffR\x03\xc8\x06@\x08\xdd\x08\x9e\t'
    b'\xe4\x08\x9a\x06f\x04#\x03\x84\x02\x91\x02z\x02}\x01`\x00\x8b\xff\xfd\xfd\x00\xfc7\xfaZ\xf8/\xf8y\xfb\xee\x02\xb7\x0c^\x16{\x1e8#\xad#\x16\x1f\xaa\x16\x86\x0c:\x02\xcb\xf9\x94\xf4\xb7\xf2\xfd\xf2\xdd\xf3\x1a\xf5\xd8\xf5G\xf4\x7f\xf1B\xef\xd1\xee\x17\xf0\xd8\xf2\xb9\xf7'
    b'\xda\xfd\x91\x03\x1b\x076\t\xf9\x08~\x05\xb5\x01\xe6\xfey\xfc\x9d\xfa5\xfb\x9b\xfd\xa1\xff\xb4\x01\xaf\x03e\x04\xce\x03\\\x03o\x03\x1f\x03l\x03\x91\x045\x06\x18\x08\xca\x08\xd4\x07\xfa\x05T\x04\xf9\x01;\xfe_\xfb,\xfai\xf9\x99\xf9N\xfb[\xfc\xd0\xfb\xb8\xfc\x92\xff\xb3\x04'
    b'!\r%\x15\x81\x1bI!L$x!\xff\x19\xef\x10[\x06\xe2\xfb\x0c\xf4\x93\xef\xc6\xed\xb6\xee\xf4\xf1\x07\xf4\x8a\xf4\x01\xf5v\xf4.\xf3\x80\xf2\xeb\xf2\xd1\xf4\xe0\xf8\xd1\xfd\xaa\x01\x07\x05\x8b\x07\xac\x07\xfa\x05N\x03\\\x00\x95\xfd\xf9\xfb)\xfc\xf6\xfc\xb1\xfe+\x01\xbf\x03\xb3\x05'
    b'N\x06\x85\x06\xa7\x06\x95\x06\xa3\x05\xe9\x04<\x05\xf7\x047\x04\xc8\x03\xfb\x02^\x01\xc0\xff]\xfev\xfc\xf3\xfa\x7f\xfa\x18\xfaw\xfaP\xfbB\xfb\x97\xfb\x9c\xfe\xc0\x05l\x0e\x83\x164\x1eF$\xf7&f$m\x1d7\x13J\x07@\xfc\x0c\xf3\x00\xed\x17\xea\xfd\xe9)\xed\xf1\xf1'
    b'\xbf\xf45\xf5$\xf7P\xf9C\xf8R\xf7z\xf9\x03\xfc\xdc\xfd/\x01\x89\x04\xd2\x04g\x04\xdb\x04\xc7\x02\xd1\xfei\xfcP\xfb:\xfaF\xfa\xca\xfb\xbb\xfd\xc2\x00\xae\x03\xa6\x05w\x07\x15\t\xab\t!\t\xb1\x08Z\x07\xad\x05\xa9\x04\xd9\x02\x95\x00p\xff\xb9\xfe\x1f\xfd3\xfc\xee\xfb'
    b"K\xfbx\xfb\xe9\xfb\x8f\xfb\xd0\xfb\xdb\xfc&\xfe<\x04\x16\x0f6\x17\x11\x1d\x96%\x0b+q'r w\x18d\x0b\x91\xfcl\xf2\xcf\xea\x0b\xe4\x9f\xe2\\\xe6e\xebG\xf0\xe4\xf4\xd6\xf8\xc2\xfc5\xff\x19\xfeC\xfd\x89\xfe\xf4\xfe\x93\xfe\xc6\xff\x01\x01\xb7\x00\x91\x01\x98\x02\x07\x01"
    b'\xa9\xfe\xdd\xfd\x89\xfd1\xfd%\xfd\xe1\xfc\x81\xfec\x02.\x05\xe5\x05\xc8\x071\n\xa5\n\x9c\ny\t\xa0\x06\x82\x04q\x03\x80\x00\x82\xfcP\xfaH\xf9\xec\xf8\xec\xf8m\xf8\x96\xf8:\xfb\xa2\xfd\xae\xfd\xc0\xfd.\x00\xb0\x06\x80\x0f\t\x17p\x1d\xe1$\x9c*|*3%\xbd\x1b'
    b'\xd4\x0e{\x01\xee\xf5m\xea-\xe0\x90\xdc\xd9\xdf\x06\xe5\xb8\xe9|\xf0`\xf9\xf7\x00\xca\x04]\x05\t\x05\xb2\x03c\x01\xfd\xfeU\xfc\x0b\xfa\x1f\xfa\x8e\xfcp\xfe\x94\xfe\x16\xff\x1e\x01\x8e\x02T\x01\x90\xfe\xb7\xfd\xc0\xfe%\xffi\xffF\x01\x8b\x04\xea\x07U\x0b\x99\r\x82\r\x9e\x0c'
    b'\x83\x0b\x84\x08\xcd\x03\x1f\xff\xc3\xfa\xfd\xf72\xf7\x1f\xf6_\xf5\xe8\xf7\x95\xfbQ\xfd\x05\xff\xde\x00U\x02y\x07\x85\x10\xd6\x16\xb9\x1bc$\xca*\xdb)\xdd%\x9b\x1f\x13\x14\x8f\x06\x0b\xfa\xe9\xec\xe7\xe1\x8c\xdcM\xdb2\xdd\xf0\xe2\xc8\xea\xa6\xf3@\xfdp\x04<\x08\x8b\n\xd1\n'
    b'\x04\x08\xfc\x03\x15\x00\x17\xfc,\xf97\xf8V\xf8y\xf9\xd1\xfb9\xfe\x9b\x00\xf7\x02\xdb\x03\xc7\x03\x04\x04\xfa\x03I\x03$\x03\xa0\x03>\x04\xa2\x05\x04\x07\xb1\x07\xe5\x07m\x07M\x06R\x04,\x01\xa5\xfd\xf9\xfa\xfe\xf8\x1f\xf7U\xf6\x12\xf7\xca\xf8w\xfb\xf5\xfd\xcf\xff\x0c\x02\xa6\x04'
    b"-\t\xef\x0f\xce\x15\xd9\x1aj!\x1a'V'\xae#\xa0\x1eJ\x16\xab\n\xdf\xfd\xc7\xf1\xa5\xe7V\xe0\r\xdd\x9a\xdd\xef\xe0!\xe7L\xf0\xc3\xf9\x9e\x00\xca\x05=\n\xd5\x0b\xb9\t\xf4\x05P\x02u\xfen\xfa\x14\xf8\xa0\xf72\xf8\xbf\xf9\xbc\xfc\xfd\xff\xe4\x01\x82\x032\x05\xcf\x05"
    b'\x14\x051\x04\x0f\x04+\x04Q\x04\xa5\x04V\x05m\x06\x1f\x07\xd5\x06\xa5\x05\xad\x031\x01p\xfe\x80\xfb{\xf8f\xf6\x1f\xf6\xc9\xf6\x1c\xf8N\xfaM\xfd\xa5\x00\t\x03\x11\x05\x8f\tB\x10j\x15\xc5\x19\xd8\x1f\xc9$\xa5%\xbd#\xb3\x1f\x0e\x18\xd8\r\xda\x02,\xf7\x04\xec\xac\xe3'
    b'\xe7\xde\xba\xdd\xcb\xdf\x92\xe4\x10\xec4\xf5\xab\xfd\x11\x04\xc5\x08\xa7\x0b\xbc\x0b\x19\t\xe9\x04\x80\x00i\xfc\xc3\xf8s\xf6(\xf6D\xf7Y\xf9\xba\xfc{\x00J\x03\x7f\x05\x98\x07\xaa\x08$\x08!\x07x\x06\xba\x05\xbd\x04\x08\x04\xc9\x03\x8f\x03\xfa\x02\x12\x02\xe6\x00A\xffB\xfd<\xfb'
    b'@\xf9\xbc\xf7\x1c\xf7K\xf7B\xf8-\xfa\xbb\xfcf\xff\r\x02\xed\x04\x92\t\x96\x0f\xbd\x14\xa5\x19*\x1f\x81#\xcc$\xc5#y \xfe\x19R\x11k\x07{\xfc\x91\xf1\xeb\xe8P\xe3i\xe0\x8f\xe0\x01\xe4`\xea\x94\xf2\x8f\xfa]\x01b\x07s\x0b.\x0c*\n\xe7\x06F\x02\xa4\xfc'
    b'\x05\xf8\xcd\xf4\xb0\xf2\x88\xf2\x0c\xf5\xea\xf8\xb5\xfc\x13\x01\xfd\x05\xa7\t3\x0b\xd1\x0b\xff\x0b\xbf\nB\x08\x16\x06}\x04\xad\x02\x1b\x01\x8c\x00d\x00\xdb\xffe\xff\xff\xfeD\xfe\n\xfd\xd1\xfb \xfb`\xfa\xf0\xf9r\xfa\xf9\xfb\xa6\xfd\xf0\xfe\xe5\x00\xbc\x03\xc7\x07\xa5\x0cv\x11\x98\x16'
    b'0\x1c\xb2 ,"\xb9!\xe1\x1f\xae\x1ar\x12=\tT\xff\x18\xf5^\xec\x18\xe6\x8c\xe2\x12\xe2\xe2\xe4s\xea\xa6\xf1&\xf9|\x001\x07\x04\x0b\xec\x0b\x19\x0bO\x08+\x03!\xfdT\xf8*\xf4-\xf1\xc1\xf0}\xf2\xbf\xf54\xfa\xa9\xff\xef\x04M\t\x89\x0c\x10\x0e=\x0e*\r'
    b'\xa6\n\xaa\x07\xc8\x04\x13\x02\xf1\xff\x91\xfe\xf3\xfd\xba\xfd\x15\xfe\xb2\xfe\xdc\xfe\xd2\xfe\x88\xfe#\xfei\xfd\x86\xfc@\xfck\xfc\xae\xfcB\xfd\xa1\xfe\x85\x00\x1b\x04\xcb\t6\x0fn\x14\xcc\x1aN \xa4"\x9a"\x0b!\x95\x1c\xf2\x14\xcc\x0b\xf7\x01\x02\xf8\r\xefR\xe8\x84\xe4z\xe3'
    b'6\xe5\xc1\xe9\x8b\xf0\x8e\xf7\xa9\xfd\xb6\x03\x96\x08\xf9\te\x08\r\x06o\x02\x9b\xfc\x14\xf7v\xf3\xcd\xf0q\xef\xdb\xf0r\xf4\x7f\xf8V\xfd?\x03l\x08\xcf\x0b\xf5\r$\x0f\xc0\x0e\xaf\x0c\xfd\t9\x07m\x04\xce\x01\xf4\xff\x14\xff\x81\xfe\x17\xfe{\xfe.\xff\x02\xff\x98\xfe\x8d\xfe'
    b'0\xfes\xfd\xf8\xfc\xd2\xfc\xe4\xfcY\xfd\xf7\xfd^\xff\xbb\x02o\x07h\x0c\xef\x11\xe8\x17\xe5\x1c\xcf\x1f\xcc {\x1fZ\x1b\x0e\x15/\r$\x04\xa7\xfaZ\xf2[\xeca\xe8\xc2\xe6$\xe8F\xec\xe2\xf1\xc1\xf7\xbf\xfd)\x03\xab\x06\x19\x08\xc2\x07\x80\x05\x93\x01d\xfd\x86\xf9\xca\xf5'
    b'y\xf3!\xf33\xf4\xb8\xf6q\xfa\x82\xfe\xa3\x02\xa6\x06_\t\x83\n\xf9\n\x85\n\xc2\x08\x9b\x06\x9d\x04\xb0\x02?\x01i\x00\x01\x00\xfb\xff)\x00q\x00\xa8\x00j\x00\x98\xff\xef\xfeU\xfeD\xfd\x95\xfc\x9b\xfc\xb8\xfc&\xfdC\xfe\xb2\xff\x8b\x02:\x07\xea\x0b\x8b\x10\xe4\x15\x8a\x1a'
    b'\x06\x1d\x93\x1d\x11\x1cI\x18\xe3\x12\xfe\x0b\xe3\x03\xf2\xfbD\xf5\x17\xf0\xc3\xec\xa3\xeb\xc7\xec\x19\xf0\xb0\xf4e\xf9\xb4\xfd\x97\x01O\x04\xf2\x04\xf4\x03\x06\x02#\xff\xc3\xfb\xee\xf8\xc4\xf6y\xf5\xb2\xf5F\xf7\xb7\xf9\xad\xfc\xc7\xff\xcd\x02\x86\x05-\x07\x97\x07\x9e\x07C\x07 \x06\xc2\x04'
    b'\xc1\x03\x17\x03\x9f\x02\x85\x02\xa1\x02\x9d\x02\x9e\x02r\x02\xe0\x01\xec\x00\xce\xff\xaf\xfe\x94\xfd\xc8\xfcd\xfcu\xfc\xf1\xfc\xbe\xfd\xd5\xfe7\x00\xce\x02\x9b\x06\x92\n\xc6\x0el\x13s\x17\xf1\x19\xd7\x1a\xd5\x19\xe5\x16d\x12n\x0c\x94\x05\xda\xfe\xd4\xf8\xe9\xf3\xd3\xf0\xb2\xef-\xf0>\xf2'
    b'\x9f\xf56\xf9Z\xfc\x17\xff\xb4\x00\xf1\x00>\x00\xbd\xfe\x81\xfcT\xfa\xd9\xf8\xc8\xf7\x87\xf7z\xf8\x1f\xfa\x1f\xfcw\xfe\xd6\x00\x9c\x02\xba\x03t\x04\xca\x04s\x04\xd2\x03\xac\x03\x9f\x03|\x03\xe9\x03\xa9\x04\x0e\x05[\x05\x92\x05\x1c\x05\x00\x04\x9c\x02\xf6\x00.\xff\x7f\xfd\x1c\xfc\x82\xfb'
    b'\x9b\xfb\xed\xfb\xcc\xfc9\xfe~\xff\xac\x00\x0e\x03O\x06+\t`\x0c;\x10s\x13;\x15\xfc\x15\x89\x151\x13r\x0f\xd2\nH\x05j\xff-\xfa\x1f\xf6g\xf3\xe6\xf1\xfd\xf1\xd2\xf3\x92\xf6J\xf9\xd2\xfb<\xfe\xd6\xffD\x00\xc3\xff\xaf\xfeH\xfd\xd7\xfb\xd6\xfa7\xfa\x19\xfa\xde\xfa'
    b'>\xfc\xb0\xfd\t\xffU\x00X\x01\xe8\x01&\x02\x0b\x02\xc2\x01\xc6\x01\x1a\x02y\x02\x12\x03\x0c\x04\x17\x05\xc1\x05\x0f\x06\xfd\x056\x05\xe6\x03d\x02\xb9\x00\xde\xfe[\xfd\xa3\xfcj\xfc\x84\xfc(\xfd=\xfeG\xff*\x00\x1f\x01\xd3\x02p\x05\x1c\x08#\x0b\xd4\x0e\x02\x12\r\x148\x15'
    b"\n\x15\xd6\x122\x0f\xb0\nR\x05\x93\xffO\xfaI\xf6\xad\xf3y\xf2\xd3\xf2\x86\xf4'\xf7)\xfa\xca\xfc\xb4\xfe\xf6\xffN\x00\x86\xff$\xfe\xb9\xfc6\xfb\x0b\xfa\xcf\xf9\xfc\xf9]\xfa\x83\xfb\xe4\xfc\xc9\xfds\xfe\xfd\xfeI\xff_\xffu\xff\xd8\xff\x9c\x00\x9a\x01\xec\x02{\x04\xdc\x05"
    b'\xed\x06g\x07H\x07\xb0\x06{\x05\xbc\x03\x0c\x02\xba\x00q\xff\x9c\xfe\x97\xfe\xd4\xfe2\xff\xe8\xff\x9e\x00\xb8\x00k\x00v\x00\xc3\x01\xdd\x032\x06\xb8\t\xf0\rc\x11\xb6\x13\xb3\x14\x9d\x13\x9b\x10m\x0c\x17\x07\x1d\x01\xb7\xfb\x94\xf7\xf1\xf4\xda\xf3\x18\xf4\xa9\xf5,\xf8\x86\xfaO\xfc'
    b'\x91\xfd\x0f\xfe\xa3\xfd\xca\xfc\xd9\xfb\xef\xfa\xa3\xfa\x06\xfb\xef\xfb(\xfd}\xfe\xc9\xff\xa3\x00\xe1\x00\x90\x00\xbb\xff\xc9\xfe\x14\xfe\xba\xfd\xd8\xfd\xa8\xfe+\x00\xc1\x01e\x03\xd3\x04o\x05\x8c\x052\x05`\x04?\x03#\x02o\x01)\x01)\x017\x01}\x01\xbf\x01\xb9\x01m\x01\xa4\x00'
    b'\xb5\xff\xf5\xfe3\xfe\xe7\xfd\x9b\xff\x01\x03\xa3\x06\xd4\ng\x0f\x8d\x12\x8e\x13\xe5\x12O\x10\xe2\x0b\xdf\x06\x1b\x02\xe8\xfd\xcd\xfa&\xf9\xbc\xf8M\xf9\x02\xfa[\xfa\x90\xfa\x94\xfa\t\xfa*\xf9\xe2\xf8<\xf9\x1e\xfa\x86\xfb8\xfd\xe2\xfe8\x00\t\x01\xf4\x00-\x00\x07\xff\xc3\xfd\xc9\xfc'
    b'C\xfc0\xfc\xa3\xfc\xc6\xfd3\xffe\x00G\x01\x15\x02\xbd\x02\x0e\x03:\x03h\x03\xc6\x039\x04\x97\x04\xd5\x04\xc5\x04c\x04\xd9\x03\x1a\x03\x00\x02\xe7\x001\x00\xc4\xffn\xff?\xff0\xff)\xff8\xffz\xff\xda\x00\x99\x03\xa8\x06%\n\xc6\r4\x10\xf8\x10A\x10\xfb\re\n'
    b'\x9c\x06\x13\x03=\x00x\xfej\xfd\xe3\xfc\x99\xfc\xf0\xfb\xc2\xfa^\xf9\xf8\xf7\xd6\xf6\x93\xf6D\xf7\xa3\xf8\xdb\xfa9\xfd\xf4\xfe&\x00\x9b\x00\x0f\x00\xe1\xfe\xd8\xfd\xef\xfcL\xfc\x7f\xfc\x14\xfd\xb9\xfdj\xfe\xea\xfe\x01\xff\xbd\xfe\x98\xfe\x9a\xfe\xdb\xfe\xcb\xff=\x01\xa7\x02\x00\x04l\x05'
    b'.\x06\x07\x06\xa6\x05\x10\x05*\x04Y\x03\xdf\x02\x91\x02K\x027\x02\x1b\x02\x7f\x01\xb6\x00\xf5\xff\x0e\xff\xad\xfe\xe9\xff\x87\x02\x84\x05\xd6\x08\x07\x0c\x01\x0e5\x0e\xc9\x0c9\n\xc8\x06j\x03\xbc\x00\xc9\xfe\xdd\xfd\x8b\xfdf\xfd2\xfdX\xfc\xdf\xfaL\xf9\xd9\xf7+\xf73\xf7\x06\xf8'
    b'\x03\xfaO\xfc%\xfeI\xff\xec\xff\xb8\xff\xed\xfeA\xfe\xa3\xfd\x83\xfd\x05\xfe\xc6\xfeH\xff\x93\xff{\xff\x03\xffu\xfe\xd7\xfd\x9c\xfd\x0c\xfe\x0c\xff*\x00t\x01\x9b\x02@\x03\x92\x03\x91\x03Z\x03\x0e\x03 \x03f\x03\xa6\x03\xe5\x03\xfd\x03\xc0\x03\x11\x03Q\x02~\x01\x9a\x00\xfe\xff'
    b'\xd3\xff\x1d\x00w\x01\x87\x03<\x05\xfe\x06N\x08\xa7\x083\x08\x10\x07\xb6\x05\\\x04m\x03\xb9\x024\x02\xd6\x01P\x01\x8a\x00Q\xff\xe4\xfd\x87\xfct\xfb\xd8\xfa\xc5\xfa\x08\xfb\x9a\xfbz\xfc\x05\xfd$\xfd>\xfd;\xfd\x0b\xfd\x19\xfdU\xfd\xb0\xfd&\xfe\x96\xfe\xde\xfe\xb3\xfez\xfe'
    b'L\xfe\x0e\xfe\xd6\xfd\x05\xfej\xfe\xd0\xfeq\xff\xdf\xffC\x00\x7f\x00\xa3\x00\xc5\x00\xce\x00\x0f\x01l\x01\xdf\x01F\x02\x9c\x02\xcc\x02\xd4\x02\xb4\x02x\x024\x02\xfd\x01\xea\x01\xd7\x01\xd7\x01\xdc\x017\x02\xa3\x02\xcf\x02\x19\x03R\x03_\x03O\x033\x03\xf9\x02\xc8\x02\xa1\x02a\x02'
    b'(\x02\xda\x01\x8b\x010\x01\xbb\x00/\x00\xb8\xffV\xff\xe9\xfe\x9e\xfe`\xfe,\xfe\x11\xfe\xff\xfd\xd1\xfd\xa9\xfd\xaf\xfd\xb2\xfd\xa5\xfd\xbb\xfd\xec\xfd\x14\xfeB\xfen\xfe\x8a\xfe\xa1\xfe\xc5\xfe\xe3\xfe\xf3\xfe\x13\xffE\xffy\xff\x9a\xff\xb9\xff\xdb\xff\xfb\xff\x0f\x00!\x006\x00J\x00'
    b'}\x00\xa0\x00\xb2\x00\xd3\x00\xf5\x00\x05\x01\x04\x01\n\x01\x15\x01\x19\x01\x1c\x01\x17\x01\x15\x01&\x01_\x01\xa3\x01\xdc\x01\x1c\x02Y\x02\x82\x02|\x02_\x025\x02\x05\x02\xde\x01\xab\x01{\x01_\x01@\x01\x0f\x01\xca\x00u\x00 \x00\xd7\xff\x89\xff8\xff\r\xff\xfb\xfe\xec\xfe\xd8\xfe'
    b'\xc2\xfe\xb8\xfe\xa5\xfe\x99\xfe\x88\xfe~\xfe\x92\xfe\xad\xfe\xcd\xfe\xe7\xfe\x06\xff&\xff6\xffA\xffK\xffZ\xffu\xff\x8e\xff\xac\xff\xcd\xff\xeb\xff\x07\x00\x17\x00\x1e\x00*\x005\x00C\x00O\x00c\x00y\x00\x8c\x00\x9f\x00\xa4\x00\xa0\x00\xa4\x00\xa5\x00\x99\x00\x91\x00\x95\x00\xa6\x00'
    b'\xe9\x00?\x01\x88\x01\xda\x01 \x02N\x02S\x02<\x02\x1b\x02\xf4\x01\xd0\x01\xaa\x01\x93\x01~\x01a\x017\x01\xf6\x00\xaa\x00S\x00\x01\x00\xb3\xffs\xffH\xff,\xff\x1e\xff\x10\xff\xfb\xfe\xea\xfe\xd7\xfe\xc2\xfe\xb4\xfe\xaf\xfe\xba\xfe\xd5\xfe\xf2\xfe\x10\xff4\xffM\xff^\xffp\xff'
    b'|\xff\x89\xff\xa2\xff\xc1\xff\xdb\xff\xf9\xff\x18\x001\x00C\x00G\x00M\x00V\x00]\x00e\x00k\x00z\x00\x8a\x00\x91\x00\x8c\x00\x84\x00\x84\x00|\x00j\x00\\\x00X\x00_\x00\x8f\x00\xc7\x00\xee\x00\x1f\x01M\x01\\\x01J\x013\x01\x0c\x01\xea\x00\xce\x00\xb2\x00\xa4\x00\x99\x00'
    b'\x8f\x00y\x00R\x00\x1d\x00\xf2\xff\xc5\xff\x99\xff|\xfff\xffh\xffp\xfft\xfft\xffs\xfft\xffn\xffk\xffk\xffu\xff\x89\xff\xa1\xff\xb4\xff\xc6\xff\xdb\xff\xe8\xff\xf0\xff\xf1\xff\xf5\xff\xfe\xff\x07\x00\x14\x00\x1e\x00*\x004\x00;\x00;\x006\x003\x000\x00/\x00'
    b"-\x00,\x00,\x00,\x00-\x00%\x00\x1c\x00\x1a\x00\x13\x00\x08\x00\x00\x00\x03\x00\x12\x001\x00O\x00g\x00\x81\x00\x93\x00\x93\x00\x84\x00p\x00X\x00H\x00:\x001\x000\x004\x009\x001\x00'\x00\x15\x00\x02\x00\xf0\xff\xdd\xff\xd1\xff\xc8\xff\xcd\xff\xd3\xff\xd8\xff\xdd\xff"
    b'\xe0\xff\xdf\xff\xd8\xff\xd3\xff\xcf\xff\xce\xff\xd0\xff\xd7\xff\xe1\xff\xec\xff\xf6\xff\xf9\xff\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xff\x01\x00\x08\x00\r\x00\x10\x00\x16\x00\x1a\x00\x19\x00%\x00*\x00&\x00,\x004\x008\x00@\x00D\x00F\x00H\x00C\x006\x00%\x00*\x00\x1e\x00\x05\x00'
    b'\x10\x00\x11\x00\x06\x00\n\x00\x08\x00\xf4\xff\xf1\xff\xe9\xff\xc8\xff\xcb\xff\xdb\xff\xf7\xff\x08\x00\x0e\x00#\x00#\x00\x16\x00\x05\x00\xf0\xff\xe2\xff\xd3\xff\xd2\xff\xe4\xff\xea\xff\xec\xff\xfe\xff\xfa\xff\xe8\xff\xe5\xff\xc7\xff\xb9\xff\xcd\xff\xca\xff\xdd\xff\x02\x00\r\x00\t\x00\x1b\x00\n\x00\xdb\xff'
    b'\xd0\xff\xb0\xff\x9f\xff\xa7\xff\xb5\xff\xe4\xff\x01\x00\x10\x00\x1e\x00\x1e\x00\x12\x00\x06\x00\xee\xff\xe6\xff\xfb\xff\x07\x00\x17\x00"\x00#\x00\x1c\x00\r\x00\xf3\xff\xe0\xff\xe2\xff\x06\x00\\\x00c\x007\x00\xed\xff\xf9\xff\t\x00\xb6\xff%\x00\xdc\xff\xcb\xffx\x00\xb9\xff\xa9\xff\xeb\xffa\xff'
    b'\x8b\xff\xec\xff\xa0\xff\xc6\xffi\x00\xe2\xff\xe2\xffP\x00\x9b\xff\xfc\xff)\x00\x83\xff\xf9\xff\xe6\xff\xbd\xff\x02\x00(\x00{\x008\x00j\x00b\x00\x0e\x00\x96\x00*\x00[\x00\x91\x00\xbf\xffV\x00\x03\x00C\xff\xb3\xff\xa4\xff\x9c\xff\x11\x00y\x00\xed\xff\xee\xffu\x00\xcc\xff\xee\xff'
    b'6\x00\xb7\xff\xfb\xff\x03\x00\xe2\xffW\x00z\x00*\x00/\x00e\x00\x01\x00\x10\x00\xff\xffs\xff"\x00\x07\x00\xa0\xffB\x00\xe4\xff\xf7\xffu\x003\x00\x14\x00C\x00\xc9\x003\x00\t\xff\x19\x00\x8a\x00I\x00\xe5\x00\xe9\xff\x83\xff\x87\x00\x01\x00\x89\xff\x8a\x000\x00l\x00\x9e\x01'
    b'\xe5\xff\xff\xff\x90\x00;\xfe\xbb\xff\xf7\x00Y\x00\x14\x02\xdc\x01*\x01\xee\xffQ\xfd\xd1\xfd\xbf\xfe\x90\xff7\x02\xe0\x02\xd9\x01O\x00\xfb\xfe\xba\xfe\x8a\xfd\xdf\xfe{\x01\xf7\x00\x97\x00\xc5\xff\x83\xfdY\xfc\x03\xfc\x9b\xfc\x16\xffq\x01\xb2\x02\xa2\x02m\x00|\x00\x95\x00_\x00\x90\x02'
    b'\xbf\x01\x11\x02\xb5\x02i\x016\x01E\xff`\xff\xe7\xff\x02\xfe\xf1\xfe\x9f\xffU\xfe\xf8\xff\xa9\x00\xd5\xfe\xcc\x00\x89\x01\x04\xff\r\x00\xef\x00\t\x00\xca\x00\x0c\x01\xfc\x00q\x00\xfa\xfep\xff\x06\xff\xaa\xfd\x9e\xfe\xd8\xfe{\xfe3\x00O\x01\x8c\x00\x95\x01+\x02*\x00\xba\x00\xf4\x01'
    b'\x96\x01N\x02\xcf\x02C\x02\xba\x00\xae\xffm\xff\x93\xfeU\xfeV\xfe\xa2\xfe\xf6\xfe\xd6\xfee\xff\x14\xff\xe3\xfeq\xffK\xff\xf8\xff\x1e\x01b\x01W\x01G\x01f\x00\x98\xff\xae\xffY\xff\x17\xff\xc9\xff\xdb\xffH\xff{\x00\xf0\x04\xf5\n`\x10\xf3\x15a\x19\x07\x18\x80\x13\x90\x0c'
    b'l\x04\xcd\xfda\xf9\xc4\xf5\xb9\xf3\x06\xf3I\xf1^\xefi\xef\x01\xf1B\xf4-\xfaf\x01!\x08\x05\r\x8c\x0f\x8b\x0f\xbf\x0c\xf3\x08\x97\x05J\x02\xae\xffu\xfe\xce\xfc\x88\xfaS\xf8m\xf6i\xf5\x15\xf5\xf2\xf6"\xfbT\xff9\x032\x07\x02\tr\x08\x86\x07\xa5\x05\xf7\x03\xe6\x02'
    b"\xc6\x01\x84\x01\x93\x00\x96\xfe\xbf\xfcV\xfaA\xf8x\xf8\xbb\xf9\x00\xfb:\xfe\xbf\x01x\x03\x1b\x04\xea\x03F\x04\x1b\x04/\x03\x10\x04\xcc\x04\xee\x03E\x03z\x01\x14\xfe`\xfc\x15\xfb?\xf9\xff\xf9\x94\xfb\x84\xfc \x00\x1c\t\xca\x14\x04\x1f}'\xb0,h*\x9d\x1e\xd7\x0e\xfa\xff"
    b'\x14\xf2\x80\xe8\xf4\xe3N\xe3_\xe5\xab\xe6\xab\xe6\xa7\xe7*\xecF\xf4\xae\xfem\x0b3\x19\x1d#7&j#v\x1bF\x10\x98\x05P\xfc\xf9\xf4J\xf2\xd2\xf0\xb4\xee]\xedV\xeb\x02\xeb\xb9\xecl\xf0\xa7\xf8\x05\x03\xee\x0b\x9b\x13b\x18\xbd\x17I\x14\xf0\ru\x06+\x02\xd8\xfe'
    b'\x9d\xfbp\xfaZ\xf9b\xf6r\xf3\xf2\xf0\xcc\xef\xb7\xf1\n\xf6\x01\xfdh\x04\x91\tF\r#\x0fs\x0c\xb9\x07n\x04\xd9\x00\x12\xff\xdb\xfeI\xfe\xb5\xfe \xfe\xcb\xfbA\xf9T\xf7\xc4\xf6\x89\xf8\x0b\xfb8\xfe/\x05-\x10*\x1c$&\xe1-\x1c0\xc1)\xf2\x1c\x1a\x0b\xd6\xf7'
    b'\xed\xe8\xa4\xdf\xd2\xda\x94\xdb\xc7\xdf\xe2\xe4\x15\xea{\xee\xae\xf4\xa0\xfd*\x08\x06\x14\xb3\x1f\xd5&\xe3(\x03%5\x1a\xc4\x0c\xbc\xfey\xf3I\xec,\xe8\x96\xe8v\xebm\xed\xea\xeek\xf1\x8b\xf3\n\xf7z\xfd=\x05\xd5\r7\x15*\x19\x07\x19\xe2\x14\x86\r]\x05\xc9\xfdr\xf8'
    b'[\xf6\xcc\xf5y\xf63\xf7\x86\xf6\xa3\xf5\xd3\xf4\xb0\xf4-\xf7\xcd\xfb\xa8\x01E\x08H\r\x83\x0f\xac\x0e\xfc\n\xdc\x05V\x00`\xfc_\xfat\xfa\r\xfc\x8d\xfd\xee\xfd\xa0\xfc]\xfb\xea\xf9\x89\xf8\x1c\xf9\xb5\xfb\x1a\x007\x06>\x11\xef\x1e\xfd(\xa7/\xd80\x06)\x17\x1aq\x06'
    b'\x1a\xf1\xf1\xe0\xe2\xd7\t\xd4J\xd7\xbb\xdf>\xe8{\xf1R\xfa%\x00`\x07\xcf\x0f\r\x18\xd1\x1fe#\x82#\\\x1f\xaf\x14\xce\x05\xa8\xf7\x8d\xec\x80\xe4\xbe\xe1\xc4\xe4f\xeb\n\xf2\xb8\xf7\xd0\xfcM\xff\\\x01\xb2\x03I\x06\xd7\x0b\xc1\x10(\x13\xf9\x14\xe9\x12C\x0bg\x03\x03\xfc'
    b'\xce\xf3A\xf0k\xf0\\\xf2\xd2\xf6\x87\xf9\xc3\xfb\x16\xfe\x1a\xfd6\xfc%\xfe\x16\x01]\x05\xef\t\xd9\x0c\xf8\x0e\xa5\r\xcb\x07\x88\x01X\xfb\xee\xf5!\xf4\x92\xf4\x0e\xf7\x9f\xfb\xa4\xfe=\x00\xfa\x00\xd6\xffe\xfe\xcd\xfe\x81\xff{\x01]\x07P\x12\r R)h.\xfd.\x8e%'
    b'\xf2\x12\x1b\xfd\x94\xe8\xf9\xd7a\xcfC\xcfG\xd7v\xe4\x7f\xf1C\xfe\x08\tK\x0f\xbb\x12\x05\x16r\x18#\x1a\x1a\x1aO\x17\xb5\x12\xc6\t\x8b\xfd \xf1\x92\xe7G\xe2\x12\xe1\xd9\xe5\xd6\xee+\xf9\x1b\x02\xd2\x07\x8b\n\xf7\n\\\td\x07\x90\x08;\nJ\x0b}\r\xf5\x0c"\x08'
    b"\xa8\x01\xf6\xf9N\xf2D\xedA\xeb-\xee'\xf5\xf4\xfaz\x00X\x06\x1b\x08\x14\x07;\x05\xee\x03k\x05\x84\x07Q\t\x07\x0c\xe5\rW\n\xe7\x02\xcf\xfb\x0b\xf4m\xed\xd2\xea\xe6\xec\xa3\xf3\x88\xfbx\x023\t\x93\r8\x0c\x90\x08\x96\x06\x0e\x04\xbb\x01\xab\x00\xfc\x00\n\x05\xc5\r"
    b'\xbe\x16\x1f\x1d "8"\xc7\x1a\xbd\x0c\x00\xfa7\xe9|\xdd\x1f\xd5\xc3\xd4\xfa\xdd\x17\xeb;\xfan\t\x1a\x144\x1a\xed\x1bu\x18A\x14\xa8\x0e\xd1\x06\xae\x02\xd0\xff\\\xfa{\xf4\xca\xf0\xd3\xee7\xed\xf3\xec\r\xf0\xf1\xf8\xf6\x00g\x06\xa2\x0c\xfb\x0f\x80\x10l\r \x08\xd6\x04'
    b'\xde\x013\xff\xa8\xfe\xfc\xfe\xda\xfd\xf4\xfb\x9c\xfa\xf3\xf7\xb4\xf4\x84\xf3\x91\xf5T\xfa\xbf\xfe\x98\x03\xcd\t\xd4\x0ee\x0f\x9d\n\x0e\x071\x04\xb6\xfeC\xfa\xe9\xf7\xb2\xf8\xe8\xfa\x82\xfbQ\xfb\x85\xfce\xfdC\xfd\xfe\xfd\xab\xfe>\x017\x05\xd4\x07O\x08\xe5\x07\x19\x07\xcf\x03\x1e\x00'
    b'\xf0\xfb\xc3\xf8\xd2\xf8,\xf9%\xfc\xec\x08\xd0\x18!#\xbd,\xcc.\x8d%\x10\x16\x92\xfeM\xe6\xea\xd5]\xcc\xdd\xca\x07\xd6:\xe73\xfa-\x0eT\x19,\x1e\x98\x1f\\\x19^\x11\n\n\xcc\x03\xb9\x01i\x00`\xfcE\xf8\x0b\xf6\xc5\xf1\x12\xecz\xeah\xed\xb7\xf3t\xfc\x92\x05'
    b'u\r\x1a\x13|\x15\xa6\x11\xfc\n\xe9\x05\xed\xff\xb6\xfc\x95\xfbE\xfa\x8f\xfc\x04\xfdy\xfa\t\xf9|\xf6\x97\xf3\x19\xf5\xd9\xf8\x1c\xfcF\x03u\x0b\xb3\x10\x9b\x12W\x0f\xb3\n\xe7\x05?\xfe\xcf\xf6\xef\xf2\xcd\xf3y\xf6\xd8\xf7q\xfbD\xfed\x00\x88\x02\xe7\x00\xba\x00\xdd\x02\xac\x04'
    b"\xbf\x05\xa6\x07\xab\x07\xcf\x05\xee\x05i\x00r\xfa,\xf9G\xf6\x86\xf6\xe0\xf7\x18\xf9\xbd\x00\x93\x10\x08 \x02(A0\xd92\xff'\x0e\x141\xf9c\xe1\xe7\xd00\xc4\xcf\xc2\xec\xcf\x01\xe4!\xfb3\x114 h'\x18)\xdd!\xba\x15%\x0cj\x01\xbd\xfa2\xf9\xb0\xf5r\xf2"
    b'\x95\xf1\xb6\xf0\xf5\xed\x91\xec\xb5\xedl\xf4}\xff\xfb\x059\r\xe1\x164\x1ao\x17f\x10\xad\x07A\x01\xb5\xfb\xbd\xf4\xda\xf0\xdb\xf3}\xf7-\xf7\xe0\xf7R\xfa\xea\xfa\x17\xfc\xc2\xfe\xf2\x00\xb4\x05\xcb\x0b\x15\x0f\x0b\x11\xe1\x0e\x12\t\xad\x04\x84\xfd\xe1\xf3(\xef\x80\xef\x8c\xf1z\xf4'
    b'm\xf9\x0f\x00\xae\x06\x1d\t\xac\x07\xfe\x07\x1b\x08\xea\x054\x03\x18\x022\x02@\x01\x05\x00\xf8\xfc\xe6\xfa\x91\xfa/\xf7\x9a\xf6Q\xf9\xae\xfbA\xff\xa9\x02\x84\x05\xf0\n\x8d\x17\xb0#\x0e*\xbe.\xbb,\t"\xc0\x0c\xb9\xf0\xde\xd8+\xc6\xe0\xbb)\xbd\xd8\xcb"\xe5"\x01\xd7\x1c'
    b'\x040\xc77\x0674,_\x1a\n\x07\xea\xf6\xb1\xec\x89\xe7\x9b\xe6\xa2\xe8T\xecK\xf0\r\xf3`\xf56\xf8f\xfe)\x06n\x0c\xdc\x14\x93\x1b\xd3\x1c\xa3\x19\xf3\x10\xef\x05\xa0\xf9\x0e\xee\x95\xe5\x0b\xe3\xe2\xe6\xbb\xeb7\xf51\x00\x8e\x06\xe0\x0br\x0f\xa3\x0fq\ro\ns\x07'
    b'#\x07\xbd\x05\xd0\xff\xbc\xfdq\xfd\x93\xf87\xf3\xb4\xf16\xf3\xa1\xf5Q\xf8F\xfcT\x04\x1d\n\xe8\n\x97\x0b9\x0b1\t\x8f\x04\xba\xff^\xfd\xbc\xfb\xde\xfaZ\xfa\x19\xfbm\xfc\xa2\xfch\xfd\xb9\xfer\xfe9\xfe\x15\x01\xcd\x02\xaa\x02\xd1\x03\xa1\x03+\x04\x0c\x07v\x0fD\x1b'
    b'\x9f"\\(\xf4&\x7f\x1d\x83\r}\xf34\xdb\xf5\xc8\x1d\xbd\x8c\xbdA\xcaV\xe2\xe7\xff\x8c\x1c\x934\x04C\xb6D\xf08\xd1%v\r\xcc\xf1\xa2\xdeC\xd2\xcc\xcc\x82\xd3\x87\xde?\xed\xa8\xfd@\nY\x12\xc5\x15\x9d\x16\x0f\x13*\x0f\x00\x0b^\x06\xcd\x06\xdb\x042\x02>\x00'
    b'$\xfb\x97\xf7U\xf2\x01\xec3\xe9\x17\xeb\xfc\xf0\x12\xf7\xf8\x00\xd9\x0b\x02\x15l\x1c\xde\x1aX\x17k\x12\xe7\x06\x85\xfbO\xf1\xa1\xea\xe0\xe6\xff\xe7B\xed\x88\xf1\x81\xfcV\x06\x80\t]\x0e\xce\x11~\x10\xe0\x0b\xb8\x08\xbf\x04z\xff\x0f\xfd\xa8\xf9\xfe\xf7\xd9\xf77\xf7\xb7\xf8\x7f\xf8'
    b'\xd0\xf9P\xfd\xfb\xfd\xf5\x00\xfa\x03w\x06\xb6\tw\t\xdb\t\xaf\x08}\x05P\x02\xa5\xfd\x01\xfa`\xf6\r\xf5\x9e\xf4L\xf6\xe7\xf9\x7f\xfb\xe5\x01\\\x06\x82\x07\xee\t\xbc\x08\x8d\x08\x98\t\x04\x10\xef\x15=\x18\xc8\x1e\xac\x1d\xc7\x14I\x07\x9b\xf5x\xe2D\xd1!\xc8\x86\xc4\xa9\xcf'
    b'\x8a\xe4\xe6\xfa\xf0\x16o.\xf9=\xcb@\xb88A)\xbb\x0fZ\xf6\xdb\xde\xea\xcf\x05\xcc\xb2\xcc\xcc\xd7B\xeb*\xfe\xdb\r)\x19\x91\x1f\xa0!\xe2\x1a\xf2\x10?\t\xc5\x00\x0f\xfb\xef\xf5o\xf5\xc1\xf7\x02\xf8\xe5\xf9W\xf8\x00\xf9\x8a\xf9\xce\xf6}\xf8>\xfa\xc1\xfe\xc7\x04\x95\t'
    b'p\x0f\x05\x12\xea\x12\x03\x11w\n\x9a\x02\xbe\xf9\xa8\xf2\n\xed\x96\xe8\x94\xea\x9a\xef\xb3\xf5\n\xff\x05\x07\x98\r\xd3\x12\xa7\x14\xbb\x11\x89\x0cC\x08\x9b\x00\xcf\xf9\x04\xf5x\xf2&\xf3\xc9\xf2\xa4\xf6\xba\xfag\xfe\xdb\x02\xff\x03\x06\x07\x01\x08\xf6\x06G\x06e\x05\x8f\x04R\x01^\x00'
    b"\x0e\x00\x0b\xfd\xe4\xfa\xa4\xfb\xc4\xfa\xb9\xf8\x8f\xfa\xb5\xfbM\xfd(\x00\x87\x01\xa0\x040\x07]\x05&\x04~\x04l\x01\xde\xfd\\\xfbO\xfa'\xfd\xae\x06\xa0\x0f\xb1\x14\x11 \x05$1\x1d\x1d\x14v\x02\xc6\xef\x16\xdf\x95\xcf\xea\xc6 \xcc6\xdcJ\xed\x12\x06:\x1f?0\xc4;"
    b' :%.\xca\x1b\x80\x04\xff\xed\xb8\xdam\xce\xa4\xcc\xc3\xd5n\xe2\x87\xf1\\\x06\x05\x16\xb4\x1dA"\x7f\x1f\x0e\x17\xbb\rv\x03\xe9\xf80\xf3{\xf2\xc4\xf0I\xf4\xf1\xf9S\xfa/\xfe\x8f\x00\xb1\xfed\xfe\xb7\xfd\x01\xfe\xf2\xff!\x03;\x05\xe7\x08\xf8\x0c\xef\x0c\xb5\n\xdb\x05'
    b"+\x02\xb4\xfc{\xf4\x82\xef\xb5\xee'\xf1\xbf\xf2\xe0\xf7F\x00\r\x07\x9f\r\r\x10\xee\x0f\x9d\x0f\xac\x0b\xd9\x042\xfe\xf4\xf8P\xf5 \xf3M\xf2\x89\xf4\x8b\xf8\xc8\xfc\xf9\x00\x9b\x04M\x07\xd3\x07\xd2\x08\xc6\x07\xd2\x03\xce\x02\xef\x01g\xfe\x19\xfc\x0e\xfd~\xfc'\xfb\x88\xfc\xa6\xfc"
    b'P\xfd\xbb\xfe\xd0\xfe\xdf\xff+\x01}\x02b\x03\\\x03\x1e\x04\x9a\x04\xe0\x02\x88\x01[\x00\xcf\xfe\x88\xfd/\xfb\x16\xfb\t\xfc\xed\xfb\xf4\xfc\xba\xfe\xde\x00\x1d\x04\n\r\x87\x15\x0b\x1a\x9a\x1f@ \x08\x1c\xf9\x10v\xff\xe1\xee \xde&\xd1T\xca\xc4\xcc\\\xd9\x85\xec8\x04D\x1a'
    b'U-\xa79l;\xfe1\xc7 \xf0\x0b?\xf3\x9a\xdf\x8b\xd1t\xca\xbf\xcf7\xdb\xb0\xebN\xfel\x0fd\x1d\x94$\x1b$\xb4\x1d\xca\x145\t>\xfdt\xf3e\xee\xb9\xedQ\xee\xfb\xf28\xf8\xf5\xfcP\x01\xae\x02^\x03\xb2\x02[\x02P\x01s\x00\x1c\x03\xac\x04\xcc\x05\xe4\x07'
    b'r\x08N\x076\x04\xa6\xffs\xfb\xa3\xf7#\xf3\x1a\xf1+\xf3d\xf6\x9b\xfa4\x00\x1d\x06\xf9\x0b-\x0fW\x0e\xe9\x0c&\n\x9b\x04>\xfe\xed\xf8g\xf5o\xf3\xb7\xf3\x82\xf44\xf87\xfe\xd4\x00I\x04w\x08@\t\xc1\x08B\x07\xeb\x04\x13\x03^\x00r\xfc\x82\xfbs\xfc\x13\xfb'
    b'\x17\xfa]\xfc\x95\xfe\x90\xfe\x1f\xff\x19\x00+\x02\xe4\x02l\x01u\x02C\x03f\x039\x02\xfe\x00\x08\x02\xe7\x00\x1d\xff\xc6\xfd\xb1\xfd\x7f\xfdr\xfbz\xfcz\xfd\xdd\xfd\x94\xff}\x00P\x02.\x03\xc0\x04_\x0b\xc0\x10\x8b\x12\xef\x14\x98\x16\xfb\x13_\n\xce\xfe\xbb\xf3%\xe8\xdd\xdf'
    b'\x8d\xd8\x94\xd9\x88\xe5 \xf1\xb2\xff#\x11\xc9 \xe6*\xc5+\xd1&\x13\x1cw\rA\xfb4\xe9t\xde\xee\xd7\xfb\xd7\xc6\xde\xab\xe9c\xf9\x99\x07\xbe\x13\xa7\x1ce\x1f\xab\x1d\x99\x16\x07\x0e\xcc\x03\x91\xf8\xf4\xf1\xf1\xed\xdf\xecs\xee)\xf2\n\xf9m\xfe\x98\x02\xa2\x05h\x07\xc1\x08'
    b'\xec\x06\xec\x04\xbc\x033\x03\xa5\x02k\x00\x05\x01\xeb\x01H\x00\x9a\xfeM\xfd\x81\xfc\r\xfa\x8c\xf8\x08\xf9\x1b\xf9\xb9\xfb\xa6\xfe\x0f\x01\x8d\x05g\x08\x89\t`\n\x1b\t\xa2\x06\xad\x02,\xfe\x15\xfb\x9a\xf72\xf5\x07\xf5\xdf\xf6\x9c\xf9B\xfcT\x01\r\x05\x02\x07\xc4\t\x8c\t\xf5\x07'
    b';\x06\xe0\x02m\xff\x91\xfc*\xfa\xa0\xf8\x1a\xf9\xbe\xf9\x9a\xfa\xb9\xfd8\x00\xf4\x01q\x03\x05\x04\x14\x05\xda\x04\xee\x02\xa1\x01\xfc\x00(\x00g\xfe\x9e\xfd\xb9\xfd\xd7\xfd{\xfe\x87\xfd;\xfe)\x006\xffM\xff\x9f\x00\n\x012\x010\x01\x84\x01O\x02G\x02\xc5\x00\xb1\x00F\x01'
    b"`\xff\x98\xfd7\xffZ\x04\x1f\x08\xf0\t\x9c\x0e\x03\x13\x7f\x11\xa8\x0b\x9f\x04\x81\xfci\xf3S\xea\xea\xe3\xfa\xe3\x04\xeaB\xf1\xfd\xfa\x10\tA\x15Q\x1cF\x1f8\x1ev\x17\x0f\x0c\x16\x00\x9f\xf3T\xe9\x9b\xe3\xe8\xe1'\xe6\xcb\xed\x12\xf7\xb0\x02\x80\rM\x14\xfd\x165\x17\xfc\x13"
    b'\x0c\r\xf6\x03K\xfb\x1f\xf6\x12\xf2\x9d\xee\xca\xef\x83\xf4\xae\xf9-\xfe\x9a\x02\xc9\x06w\t\x8e\t\xa5\x06\xff\x04\xcb\x03\xa9\xffM\xfdp\xfdR\xfd\xb9\xfd~\xfe\x91\xff1\x01(\x01]\xff%\xffD\xff!\xfd\x80\xfb\xdd\xfcn\xfe\x0b\xff\xbf\x00\xf7\x02\xd8\x05\x9a\x06+\x05\xf7\x04'
    b'\x98\x03\xea\x00/\xfdZ\xfa\x14\xfa\xa5\xf8b\xf8\\\xfaA\xfdu\x00;\x02U\x05\xb6\x07\xb6\x07\x08\x07A\x05\xb3\x03\xb6\x00H\xfd\xfe\xfa\xd1\xf9\xe4\xf9\x0e\xf9\x87\xfam\xfdq\xff\xe0\x01\x13\x03\x12\x05\xe8\x05\xa4\x04$\x04a\x02\xdf\x00\x14\xff9\xfd\x01\xfd#\xfc\xaa\xfc_\xfd'
    b"\xb8\xfd\xd6\xff[\x00\xb6\x00\xed\x01\x11\x02\xbd\x01\x1e\x01^\x01\xd9\x00\xe6\xff\xe0\xff\xcd\xff\x06\x00j\xff[\xff\xcb\xff\x80\xffk\xff\xd6\xfe9\xff\x9b\xff\xd3\xfe1\xff\x12\x01\x08\x05\x11\x08\xc3\t\xbc\r\x17\x0f\xcd\x0c\xa8\t\x0e\x03\xe0\xfbO\xf5'\xee\xbf\xe9\xab\xe9J\xed/\xf3"
    b'\xbe\xfb\r\x06\xe7\x0e\xa4\x15\xdd\x18\x15\x18\xc9\x13\xdd\x0b\xe5\x02H\xf9\xcb\xf0\x97\xeb\x11\xe9\xc7\xeaL\xef\x0b\xf6\xb4\xfec\x06\xdd\x0c\xd5\x10K\x12\xf2\x10z\x0c\x0c\x07\xa7\x009\xfb\xd3\xf6 \xf3S\xf32\xf5^\xf7D\xfb\xac\xff\x8d\x03\xce\x05!\x07\x82\x079\x06\x98\x04\x13\x02'
    b'\xec\xff\xa8\xfe\x1a\xfd\xf3\xfcL\xfd\xe2\xfd\xfa\xfev\xff_\x00\x8a\x00\r\x00\xbc\xff]\xff?\xffV\xfe\xc2\xfe\xeb\xffA\x00[\x01\x14\x02\xfb\x02e\x03\xbb\x02\xfa\x01\xa8\x00\x97\xff\xe4\xfd[\xfc8\xfc\xe4\xfb(\xfc|\xfd\x01\xff\xbc\x00\x18\x02g\x03[\x04[\x04\xea\x03k\x02'
    b"H\x01\x14\x00\xae\xfd\xb4\xfc[\xfc\xf7\xfbd\xfc'\xfd\xe9\xfe{\x00d\x01`\x02r\x03\xaa\x03\xaf\x02\x06\x02O\x01\xfa\xff\xe7\xfe\xfd\xfd\x8b\xfd\xdb\xfd\xe1\xfd\x0b\xfeM\xff>\x00b\x00\xed\x00\xb2\x01\x8d\x01\t\x01\x17\x01\x96\x00\x00\x00\xef\xff\x89\xffR\xff\x8d\xff\x97\xff\x80\xff"
    b'\xd3\xff\xfb\xff\xb4\xff\xd8\xff\x1a\x00\xb5\xff\x91\xff\x04\x00\x06\x00\x12\x00E\x00j\x00\xc8\x00\xe7\x00\x9e\x00N\x00o\x00\x13\x00F\xff\x94\xff\xe0\x00\xdd\x01m\x02\xd9\x03\x1f\x05\xee\x04\xf0\x03\x84\x02{\x00\xd3\xfd\x83\xfb\xbd\xf9\xa5\xf8I\xf9\xd0\xfa\xcd\xfc\xf3\xff<\x03\xc2\x05u\x07'
    b'(\x08\xa1\x07\xa0\x05\x11\x03\xfe\xff\x88\xfch\xfa\xce\xf8\x00\xf8\x01\xf9\xcc\xfaZ\xfd#\x00\xd6\x02\xf7\x04A\x06\xc8\x06\xb5\x05+\x04-\x02\x06\x00\xcf\xfd\xb8\xfb\x80\xfbo\xfb\xd6\xfb=\xfd\xdb\xfe\xcf\x00\xd6\x01\xae\x02-\x03\xf8\x02Y\x02\xf3\x00!\x00\x80\xff\xa1\xfeX\xfe_\xfe'
    b'\x17\xff\xae\xff\xd8\xff\xa6\x00\xc6\x00\xbf\x00\xa2\x00\xd6\xff\xa3\xff-\xff\xee\xfe\xfa\xfe3\xff\xe6\xff8\x004\x01\x91\x01\x84\x01\xe2\x01*\x01\xb3\x00\xd4\xff\xc6\xfes\xfe\xd6\xfd\xd8\xfd\xe4\xfd\xa8\xfe\xe0\xff@\x00`\x01\x0f\x02S\x02\x88\x02\x9c\x019\x01j\x00-\xff\xaa\xfe\xdf\xfd'
    b'\xda\xfd\xed\xfdG\xfe9\xff\xb9\xff\xe9\x00M\x01\x88\x01,\x02\x87\x01-\x01\xa7\x00\xec\xffz\xff\xbe\xfe\xac\xfe\xad\xfe\xee\xfeA\xfft\xff]\x00\x98\x00\xb0\x00\xe4\x00\xa2\x00\xc8\x006\x00\xbe\xff\xcd\xff\x84\xff\x9b\xffd\xff\xb6\xff/\x00\xfc\xffd\x00N\x00S\x00d\x00\xcc\xff'
    b'\xe1\xff\xb5\xff\x82\xff\x88\xff\x9d\xff\xf4\xff\xe9\xffZ\x00\x95\x00t\x00\xba\x00s\x00J\x00\x1b\x00\x9f\xff\x82\xff\\\xffx\xffS\x005\x01\xd9\x01\xb6\x02N\x03S\x03\xb8\x02\x85\x01\x05\x00\x89\xfe=\xfd\xe4\xfbf\xfb\x08\xfc\xfd\xfcT\xfe-\x00&\x02\x99\x03\x87\x04\xc9\x04+\x04'
    b'\x0f\x03\x88\x01\x87\xff\xce\xfd\x93\xfc\xb5\xfb\xb7\xfb4\xfcM\xfd\xfb\xfev\x00\xdd\x01\xf5\x02\x80\x03\x8a\x03\xfe\x02\xd2\x01\xb0\x00\xba\xff\x87\xfe\xad\xfd{\xfd\xbd\xfd\x18\xfe\xb4\xfe\x83\xffI\x00\x04\x01*\x012\x01=\x01\xf6\x00\x84\x00\x10\x00\xf5\xff\xcf\xff\xa8\xff\xc9\xff\xe2\xff\xfc\xff'
    b'\n\x00\xff\xff\xe4\xff\xaf\xff\x85\xffc\xffO\xffZ\xff\x99\xff\xf3\xffK\x00\xb6\x00\xff\x004\x01;\x01\xef\x00\x94\x00#\x00\x91\xff\x07\xff\xbd\xfe\x93\xfe\x97\xfe\xed\xfeh\xff\xe3\xfft\x00\x14\x01G\x01X\x01_\x01\x00\x01\x8f\x00\x04\x00|\xff.\xff\xe4\xfe\xc8\xfe\xed\xfe8\xff'
    b'\xa0\xff\xfd\xff]\x00\xa3\x00\xde\x00\xd9\x00\xaa\x00\x8f\x00:\x00\x06\x00\xc5\xff\x84\xff\x9c\xff\x91\xff\x9a\xff\xbf\xff\xe5\xff\x0b\x00\x0b\x00\x1f\x00#\x00\x14\x00\x16\x00\xfe\xff\x0b\x00\t\x00\xff\xff(\x00\x14\x00!\x000\x00\n\x00\x0e\x00\xe9\xff\xd7\xff\xcb\xff\xab\xff\xba\xff\xb7\xff\xde\xff'
    b'\xf9\xff\n\x00I\x00O\x00V\x00a\x00G\x005\x00\x01\x00\xde\xff\xcb\xff\xaa\xff\xab\xff\xa0\xff\xbf\xff\xdf\xff\xec\xff?\x00\xb6\x00&\x01X\x01\x7f\x01\xaa\x01`\x01\xce\x00\x17\x00d\xff\xce\xfe<\xfe\xee\xfd\r\xfe\x91\xfe0\xff\xe5\xff\xc3\x00o\x01\xe3\x01\x0c\x02\xc7\x01e\x01'
    b'\xc7\x00\x06\x00S\xff\xbe\xfe\x84\xfei\xfe\x89\xfe\xf1\xfen\xff\x00\x00u\x00\xce\x00\t\x01\x07\x01\xf4\x00\xb5\x00R\x00\x0f\x00\xd7\xff\xaa\xff\x84\xff|\xff\xa5\xff\xba\xff\xd0\xff\xe0\xff\xf8\xff\r\x00\xfc\xff\xf9\xff\xfe\xff\x0b\x00\x16\x00\x19\x00B\x00Q\x00W\x00_\x00@\x00-\x00'
    b'\x00\x00\xcb\xff\xa9\xff|\xffx\xff|\xff\x9a\xff\xc6\xff\xf7\xff?\x00f\x00\x84\x00\x93\x00\x82\x00r\x006\x00\xfd\xff\xd5\xff\xac\xff\x90\xffz\xff\x97\xff\xb4\xff\xc8\xff\xfa\xff\x1e\x00>\x00I\x00M\x00O\x004\x00&\x00\x0b\x00\xf6\xff\xf0\xff\xdc\xff\xdd\xff\xdc\xff\xe5\xff\xea\xff'
    b"\xe0\xff\xfc\xff\xff\xff\xee\xff\xfa\xff\x0e\x00\x0e\x00\x04\x00\x16\x00'\x00%\x00\x1e\x00\x14\x00\x16\x00\n\x00\xf0\xff\xe4\xff\xd7\xff\xd9\xff\xd7\xff\xcb\xff\xe9\xff\xf4\xff\x08\x00)\x00,\x00F\x00E\x00:\x005\x00\x0e\x00\xf6\xff\xdb\xff\xc8\xff\xbe\xff\xb5\xff\xc3\xff\xd8\xff\xf9\xff\x0c\x00"
    b'\x1c\x00:\x00?\x009\x000\x00\x17\x00\x0b\x00\xfb\xff\xde\xff\xd7\xff\xdc\xff\xdc\xff\xdf\xff\xf0\xff\xff\xff\x07\x00\x08\x00\x0e\x00*\x00l\x00\x92\x00\x97\x00\xc1\x00\xc3\x00\x89\x00<\x00\xd3\xff\x81\xff=\xff\xef\xfe\xdf\xfe \xffu\xff\xd5\xff@\x00\xb5\x00\n\x01&\x01\n\x01\xcf\x00'
    b'\x88\x00\x16\x00\xa8\xffX\xff$\xff \xff)\xffZ\xff\xac\xff\xf4\xff@\x00s\x00\x97\x00\xa0\x00\x8b\x00t\x00@\x00\x10\x00\xe3\xff\xc0\xff\xae\xff\x97\xff\xa1\xff\xbb\xff\xd5\xff\xef\xff\x00\x00 \x002\x00*\x00&\x00$\x00 \x00\x1c\x00\n\x00\t\x00\x13\x00\x05\x00\xf8\xff\xec\xff'
    b'\xe1\xff\xd0\xff\xbf\xff\xb7\xff\xbd\xff\xd9\xff\xee\xff\n\x007\x00T\x00f\x00c\x00S\x00@\x00\r\x00\xe2\xff\xb6\xff\x94\xff\x8d\xff\x86\xff\x9a\xff\xc3\xff\xee\xff \x00J\x00m\x00z\x00v\x00o\x00H\x00\x1c\x00\xf4\xff\xd0\xff\xbd\xff\xa8\xff\xa8\xff\xc0\xff\xd9\xff\xf5\xff\x02\x00'
    b"\x19\x008\x001\x00 \x00%\x00%\x00\x19\x00\t\x00\x08\x00\x00\x00\x00\x00\xf2\xff\xd3\xff\xde\xff\xe4\xff\xf1\xff\xfc\xff\x05\x00)\x004\x00/\x00!\x00\r\x00\x00\x00\xd7\xff\xbc\xff\xc1\xff\xc1\xff\xcd\xff\xe7\xff\x06\x00 \x003\x00+\x00$\x00'\x00\t\x00\xf4\xff\xf8\xff\xee\xff"
    b'\xe2\xff\xf4\xff\xef\xff\xdf\xff\xed\xff\xe7\xff\xde\xff\xe8\xff\xf0\xff\xff\xff\x17\x00"\x00#\x000\x001\x00\x1f\x00\x04\x00\xf2\xff\xe5\xff\xdd\xff\xd4\xff\xd1\xff\xdc\xff\xf5\xff\x02\x00\x07\x00\x19\x00\x18\x00"\x00 \x00\x0b\x00\x01\x00\xf7\xff\xeb\xff\xdb\xff\xd7\xff\xd3\xff\xde\xff\xf6\xff\xf9\xff'
    b'\x0b\x00"\x00$\x00+\x00\x1d\x00\r\x00\x00\x00\xec\xff\xdc\xff\xcc\xff\xd9\xff\xea\xff\xf4\xff\x0f\x00!\x006\x00B\x002\x00/\x00\x19\x00\xfd\xff\xec\xff\xcb\xff\xbd\xff\xb2\xff\xb9\xff\xcc\xff\xe1\xff\n\x00 \x00>\x00Z\x00U\x00M\x007\x00\x16\x00\xfa\xff\xd3\xff\xbf\xff\xbf\xff'
    b"\xc9\xff\xd6\xff\xed\xff\x15\x00-\x009\x003\x00+\x00&\x00\t\x00\xee\xff\xdc\xff\xd1\xff\xd0\xff\xcf\xff\xd7\xff\xef\xff\x06\x00\x19\x00,\x00>\x00<\x00/\x00\x1b\x00\xfd\xff\xe2\xff\xc6\xff\xbc\xff\xc5\xff\xd0\xff\xe6\xff\xfc\xff\x19\x00-\x00*\x001\x00'\x00\x1f\x00\x18\x00\xfe\xff"
    b'\xf6\xff\xf3\xff\xe7\xff\xe3\xff\xd9\xff\xdb\xff\xdd\xff\xdd\xff\xe1\xff\xef\xff\t\x00\x1d\x00/\x00@\x00G\x00M\x007\x00\x1e\x00\x0b\x00\xea\xff\xd4\xff\xba\xff\xaa\xff\xaa\xff\xaf\xff\xc7\xff\xe7\xff\r\x004\x00W\x00o\x00n\x00a\x00F\x00\x1a\x00\xee\xff\xba\xff\x95\xff\x86\xff\x87\xff'
    b'\x9c\xff\xc0\xff\xf9\xff+\x00Y\x00y\x00y\x00q\x00X\x00%\x00\xf7\xff\xc6\xff\xa4\xff\x8d\xff\x8b\xff\x9b\xff\xbb\xff\xed\xff\x1a\x00D\x00k\x00x\x00o\x00S\x003\x00\t\x00\xd5\xff\xba\xff\xae\xff\xaf\xff\xbd\xff\xd9\xff\xff\xff!\x009\x00E\x00G\x00;\x00 \x00\x00\x00'
    b'\xe5\xff\xd1\xff\xcb\xff\xd3\xff\xe1\xff\xf9\xff\x0c\x00\x1d\x00(\x00\x1c\x00\x0c\x00\xfa\xff\xe7\xff\xd5\xff\xca\xff\xd4\xff\xe9\xff\xfc\xff\x14\x00,\x00A\x00G\x009\x00 \x00\x03\x00\xea\xff\xc2\xff\xae\xff\xb0\xff\xb4\xff\xce\xff\xeb\xff\x08\x00(\x00<\x00C\x00:\x00/\x00\x1d\x00\x07\x00'
    b'\xfd\xff\xe8\xff\xe0\xff\xe8\xff\xe6\xff\xea\xff\xec\xff\xf4\xff\xfa\xff\xf4\xff\xfb\xff\x00\x00\x0b\x00\x11\x00\x13\x00\x1e\x00\'\x00"\x00\x18\x00\x0e\x00\x02\x00\xf6\xff\xe7\xff\xda\xff\xd8\xff\xdb\xff\xde\xff\xed\xff\x00\x00\x13\x00&\x003\x00=\x006\x00"\x00\x0f\x00\xfa\xff\xe4\xff\xd5\xff\xcf\xff'
    b"\xd5\xff\xde\xff\xf0\xff\x03\x00\x10\x00\x1e\x00%\x00&\x00\x1c\x00\x0b\x00\xfe\xff\xec\xff\xda\xff\xd1\xff\xd2\xff\xde\xff\xef\xff\xff\xff\x10\x00'\x002\x007\x00.\x00\x1e\x00\x11\x00\xfc\xff\xee\xff\xdf\xff\xd7\xff\xdd\xff\xe5\xff\xed\xff\xf9\xff\x06\x00\x11\x00\x1e\x00 \x00\x1c\x00!\x00\x1b\x00"
    b"\n\x00\x00\x00\xfb\xff\xf6\xff\xf4\xff\xf1\xff\xf1\xff\xf6\xff\xf8\xff\xfe\xff\xfe\xff\x02\x00\x05\x00\x07\x00\x0b\x00\t\x00\x0f\x00\x11\x00\x10\x00\x13\x00\x10\x00\x0f\x00\x0b\x00\x01\x00\xfd\xff\xf8\xff\xef\xff\xec\xff\xec\xff\xe8\xff\xeb\xff\xf4\xff\xfa\xff\x02\x00\x0e\x00\x15\x00\x1d\x00$\x00'\x00(\x00"
    b' \x00\r\x00\xff\xff\xeb\xff\xd6\xff\xc7\xff\xbd\xff\xc8\xff\xd9\xff\xed\xff\x05\x00$\x00B\x00N\x00K\x00B\x000\x00\x12\x00\xf5\xff\xd8\xff\xc0\xff\xb6\xff\xb6\xff\xbc\xff\xd1\xff\xf0\xff\t\x00\'\x009\x00B\x00E\x005\x00"\x00\r\x00\xf3\xff\xdf\xff\xd6\xff\xd1\xff\xd8\xff\xe1\xff'
    b'\xe8\xff\xfe\xff\x0e\x00\x15\x00\x1a\x00\x1d\x00\x1a\x00\x13\x00\x0b\x00\x00\x00\xfd\xff\xf5\xff\xf2\xff\xf4\xff\xfa\xff\xfc\xff\xfb\xff\xfe\xff\xfd\xff\xfc\xff\xf9\xff\xf9\xff\xfc\xff\xfe\xff\x03\x00\x05\x00\n\x00\x0e\x00\x12\x00\x11\x00\x11\x00\x08\x00\x00\x00\xfb\xff\xf2\xff\xed\xff\xe7\xff\xeb\xff\xf2\xff\xff\xff'
    b'\n\x00\x10\x00\x1d\x00!\x00\x1c\x00\x17\x00\x0c\x00\xfe\xff\xf3\xff\xe7\xff\xe4\xff\xe5\xff\xe5\xff\xef\xff\xff\xff\t\x00\x14\x00\x19\x00\x1c\x00\x15\x00\x0e\x00\x01\x00\xf9\xff\xf3\xff\xee\xff\xef\xff\xf7\xff\xff\xff\x03\x00\x07\x00\x11\x00\x11\x00\n\x00\t\x00\x06\x00\x02\x00\xfd\xff\xfc\xff\xfd\xff\x00\x00'
    b'\x03\x00\x06\x00\t\x00\t\x00\x02\x00\x00\x00\xfe\xff\xf6\xff\xf0\xff\xf2\xff\xf6\xff\xfb\xff\xfe\xff\x08\x00\x0f\x00\x14\x00\x13\x00\x11\x00\x10\x00\x04\x00\xfd\xff\xf2\xff\xeb\xff\xea\xff\xe7\xff\xea\xff\xf4\xff\xfb\xff\x06\x00\x0f\x00\x16\x00\x19\x00\x18\x00\x17\x00\x0f\x00\x05\x00\xfe\xff\xf7\xff\xf3\xff\xf1\xff'
    b'\xf1\xff\xf7\xff\xfd\xff\x01\x00\x03\x00\x07\x00\x0c\x00\t\x00\x05\x00\x07\x00\x04\x00\x01\x00\x00\x00\xff\xff\xfc\xff\xfe\xff\xfc\xff\xf9\xff\xfd\xff\x00\x00\x06\x00\x07\x00\x08\x00\x0c\x00\x0c\x00\x07\x00\x02\x00\xff\xff\xfa\xff\xf3\xff\xf0\xff\xf5\xff\xf6\xff\xf8\xff\xff\xff\x03\x00\t\x00\x0c\x00\x08\x00\t\x00'
    b'\t\x00\x04\x00\x02\x00\x00\x00\xfa\xff\xf9\xff\xf8\xff\xf6\xff\xf7\xff\xfb\xff\xfd\xff\x00\x00\x03\x00\x03\x00\x06\x00\x04\x00\x04\x00\x05\x00\x01\x00\x01\x00\x02\x00\x01\x00\x01\x00\x00\x00\xfc\xff\xff\xff\xff\xff\xfe\xff\xfe\xff\xfd\xff\xfe\xff\xff\xff\xff\xff\x01\x00\x03\x00\x04\x00\x02\x00\x08\x00\x06\x00\x06\x00'
    b'\x00\x00\x00\x00\x00\x00\xfc\xff\xff\xff\xfc\xff\xfc\xff\xff\xff\xff\xff\x01\x00\x01\x00\x02\x00\x00\x00\xfe\xff\x02\x00\x03\x00\x04\x00\x04\x00\x02\x00\x06\x00\x06\x00\x05\x00\x06\x00\x04\x00\x06\x00\x06\x00\x02\x00\x01\x00\xff\xff\x00\x00\xff\xff\x00\x00\x01\x00\x01\x00\x01\x00\x04\x00\x03\x00\x03\x00\x04\x00\x04\x00'
    b'\x02\x00\x00\x00\x00\x00\xff\xff\xfe\xff\xfc\xff\xff\xff\xfc\xff\xfc\xff\xfc\xff\xfd\xff\x00\x00\x00\x00\x01\x00\x03\x00\x03\x00\x00\x00\xfd\xff\xfd\xff\xf8\xff\xf8\xff\xf9\xff\xfc\xff\xfc\xff\x00\x00\x05\x00\x02\x00\x05\x00\x05\x00\x04\x00\x03\x00\x00\x00\xfb\xff\xf8\xff\xf7\xff\xf3\xff\xf5\xff\xf8\xff\xfd\xff\xfe\xff'
    b'\x03\x00\x08\x00\x05\x00\x06\x00\x05\x00\x02\x00\x00\x00\xfe\xff\xfc\xff\xfd\xff\xf9\xff\xfa\xff\xfa\xff\xfb\xff\xff\xff\x01\x00\x02\x00\x02\x00\x05\x00\x01\x00\x03\x00\x00\x00\xfe\xff\xfe\xff\xf9\xff\xf9\xff\xfc\xff\xfb\xff\xfb\xff\xfd\xff\xfe\xff\x00\x00\x01\x00\x02\x00\x03\x00\x01\x00\x00\x00\xff\xff\xfe\xff\xff\xff'
    b'\xff\xff\xfe\xff\xfe\xff\xfe\xff\xfd\xff\xfd\xff\xfd\xff\xfd\xff\xfd\xff\x00\x00\xfe\xff\x01\x00\x02\x00\x03\x00\x04\x00\x03\x00\x03\x00\x02\x00\x00\x00\x00\x00\x00\x00\xfd\xff\xfa\xff\xfd\xff\xff\xff\x00\x00\x02\x00\x02\x00\x02\x00\x02\x00\x02\x00\x02\x00\xff\xff\xfe\xff\x00\x00\x00\x00\xfd\xff\xff\xff\xff\xff\xfc\xff'
    b'\xff\xff\x00\x00\xff\xff\x01\x00\x01\x00\x03\x00\x04\x00\x02\x00\x02\x00\x02\x00\x01\x00\xff\xff\xfd\xff\xfa\xff\xf8\xff\xf7\xff\xfb\xff\xfc\xff\xff\xff\x00\x00\x02\x00\x05\x00\x06\x00\x04\x00\x01\x00\x00\x00\xfc\xff\xfa\xff\xf9\xff\xf7\xff\xfa\xff\xfa\xff\xfa\xff\x00\x00\x02\x00\x05\x00\x04\x00\x04\x00\x04\x00\x05\x00'
    b'\x01\x00\x00\x00\xfe\xff\xfd\xff\xff\xff\xff\xff\xfd\xff\x00\x00\x00\x00\x00\x00\x02\x00\x03\x00\x05\x00\x04\x00\x04\x00\x05\x00\x01\x00\xfe\xff\xfe\xff\xff\xff\xff\xff\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x03\x00\x00\x00\x01\x00\xff\xff\xff\xff\xff\xff\xfc\xff\xfe\xff\x00\x00\xfe\xff\x00\x00\x00\x00\x00\x00\x02\x00'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x00\x01\x00\x03\x00\x00\x00\x00\x00\x01\x00\xff\xff\xfe\xff\xfd\xff\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\x00\x00\x03\x00\x02\x00\x01\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x02\x00\x02\x00\x00\x00\x01\x00\x02\x00'
    b'\x02\x00\x01\x00\xff\xff\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x01\x00\x01\x00\x02\x00\x00\x00\x03\x00\x01\x00\x00\x00\x02\x00\x01\x00\x00\x00\x01\x00\x01\x00\x00\x00\xff\xff\xfd\xff\xfe\xff\x00\x00\xfe\xff\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff'
    b'\xfe\xff\x00\x00\xfd\xff\xfe\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xff\xfe\xff\xfe\xff\xfc\xff\xfd\xff\xfe\xff\x00\x00\xfe\xff\x00\x00\x02\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\xfe\xff\xff\xff\xfe\xff\xfe\xff\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\xff\xff\x01\x00'
    b'\xff\xff\xff\xff\x00\x00\xfd\xff\xfd\xff\x00\x00\xfe\xff\xfe\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xfe\xff\xff\xff\xff\xff\xfe\xff\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\xff\xff\x00\x00\x00\x00'
)

# BEGIN vision_protocol.py
"""PC／MicroPython共用20字节编码器及受限发送器，无导入时串口副作用。

唯一规格为control/docs/protocol_v1_draft.md。本模块不扩字段、不自动
发送START或STOP。路径新鲜度、处理超限、无当前观测均编码为新序号
无效包；历史方向、近场中点和终点观察门不可冒充固定y120偏差。
"""

try:
    import ustruct as struct
except ImportError:
    import struct


def crc16(data):
    """CRC-16/CCITT-FALSE；校验范围0..17字节，结果小端写入18..19。"""
    crc=0xffff
    for byte in data:
        crc^=byte<<8
        for _ in range(8):
            crc=((crc<<1)^0x1021)&0xffff if crc&0x8000 else (crc<<1)&0xffff
    return crc


def encode_path(sequence,error=0,valid=False,confidence=0,heading=0,bend=0,processing_ms=0,finish=False):
    """按原协议编码；偏差右正，heading单位0.01度，耗时毫秒。

    heading／bend没有经验证定义时保持0；绝不把C2左右提示强行量化为
    物理角度或500以上的弯强度（主控会因此改变演示基础请求）。
    """
    if not (0<=sequence<=255 and -1000<=error<=1000 and 0<=confidence<=100 and
            -9000<=heading<=9000 and 0<=bend<=1000 and 0<=processing_ms<=1000):
        raise ValueError('path field out of protocol range')
    head=bytes((0xa5,0x5a,1,1,12,sequence))
    body=struct.pack('<BBhhHHBB',int(bool(valid))|(int(bool(finish))<<1),confidence,
                     error,heading,bend,processing_ms,0,0)
    data=head+body
    return data+struct.pack('<H',crc16(data))


def encode_command(sequence,command):
    """1 START／2 STOP／3 STATUS；本函数只编码，不解释为实际执行许可。"""
    if not 0<=sequence<=255 or command not in (1,2,3):raise ValueError('bad command')
    data=bytes((0xa5,0x5a,1,2,12,sequence))+bytes(10)+bytes((command,0))
    return data+struct.pack('<H',crc16(data))


class RecognitionSender:
    """两种type独立递增，0..255回绕；调用者注入writer，不自动打开端口。

    allow_valid_path默认False：板上诊断核未完成C2关联验证，不能发可信
    路径。电脑离线交叉验证可显式置True，但不会连接真实串口。
    """

    def __init__(self,writer=None,allow_valid_path=False):
        self.writer=writer
        self.allow_valid_path=allow_valid_path
        self.path_sequence=0
        self.command_sequence=0

    def _send(self,data):
        """短写继续发送剩余字节；不重复整包，0／None立即报错避免死循环。

        写入长度不是对端接收／CRC正确证明；故障时停止应用并让STM32
        既有200ms断流逻辑生效，不能用这项软件处理宣称车辆已停稳。
        """
        if self.writer is None:return data
        offset=0
        while offset<len(data):
            count=self.writer(data[offset:])
            if not isinstance(count,int) or not 0<count<=len(data)-offset:
                raise OSError('UART short/failed write')
            offset+=count
        return data

    def path(self,result,finish=None,processing_ms=0,source_age_ms=None):
        """将真实C2当前固定行结果映射原协议，其余状态只能发无效。

        source_age_ms为采集开始到发送前的保守本地年龄，必须用真实时间。
        旧录制离线生成包的年龄0仅模拟字节映射，不宣称实时新鲜。处理
        超100ms或年龄≥200ms立即无效；超1000ms只饱和字段，不隐瞒超限。
        """
        age_known=source_age_ms is not None
        if not age_known:source_age_ms=200  # 年龄未知不默认为新鲜，可信路径关闭。
        if (not isinstance(processing_ms,(int,float)) or not isinstance(source_age_ms,(int,float)) or
                processing_ms<0 or source_age_ms<0 or processing_ms!=processing_ms or
                source_age_ms!=source_age_ms or processing_ms==float('inf') or source_age_ms==float('inf')):
            raise ValueError('finite nonnegative processing and age required')
        obs=result.get('recovery_observation',{})
        valid=bool(age_known and self.allow_valid_path and result.get('valid') and obs.get('fixed_reference_observed') and
                   obs.get('temporal_state')=='stable_observation' and processing_ms<=100 and source_age_ms<200)
        error=result.get('deviation_normalized') if valid else 0
        if valid and (not isinstance(error,int) or not -1000<=error<=1000):
            raise ValueError('valid current y120 normalized deviation required')
        confidence=max(0,min(100,round(result.get('quality',0)*100))) if valid else 0
        f=finish or {}
        finish_flag=bool(age_known and source_age_ms<200 and processing_ms<=100 and
                         f.get('observation',{}).get('visible') and f.get('state')=='finish_line_seen')
        data=encode_path(self.path_sequence,error=error,valid=valid,confidence=confidence,
                         heading=0,bend=0,processing_ms=min(1000,int(processing_ms+.999)),finish=finish_flag)
        self.path_sequence=(self.path_sequence+1)&255
        return self._send(data)

    def command(self,command):
        """仅供明确的人工无动力联调触发；识别循环不调用此方法。"""
        data=encode_command(self.command_sequence,command)
        self.command_sequence=(self.command_sequence+1)&255
        return self._send(data)

# BEGIN lite_lap_route.py
"""L1独立试跑候选：稀疏灰度网格＋当前二维道路模板，无NumPy/OpenCV。

复用昨晚的道路几何思路，重新限制搜索和内存；不导入或修改T2/BP1。
输入320×240连续灰度缓冲、会话内真实毫秒。当前黑组件、双边／单边关联
和短历史分别输出，不把画外模板当实测。平面横向比例仍未实测，全部输出
都是试跑候选，须先板上计时和现场无动力目视核对，不能称已安全可控。
"""
import math
from array import array

WIDTH = 320
HEIGHT = 240
GRID_STEP=6  # 电脑全量对照保持4；实板合并包显式生成6像素网格以降低已测网格耗时。
GW = WIDTH//GRID_STEP
GH = HEIGHT//GRID_STEP
GY0=(40+GRID_STEP-1)//GRID_STEP
GY1=(228-3)//GRID_STEP+1


def _hypot(x,z):
    """使用MicroPython基础sqrt，不依赖部分固件未提供的math.hypot。"""
    return math.sqrt(x*x+z*z)


def _pixel(x, z):
    """候选地面cm→像素；沿用中央20/40/60cm标定＋未验横向gain48。

    原点在车头投影。返回None代表画外，绝不夹到画面边缘制造假观测。
    这里只复用几何假设，不把一维留出验证外推为全图准确性。
    """
    if z <= 2:
        return None
    y = (7802.22222222222 - 38.11111111111108*z)/(z+15.555555555555546)
    px = 159.5+x*(y+38.11111111111108)/48.
    if not (4 <= px < 316 and 40 <= y < 228):
        return None
    return int(y)//GRID_STEP*GW+int(px)//GRID_STEP


def _point(cx, cz, u, v, s):
    direction = u if s < 0 else v
    return cx+s*direction[0], cz+s*direction[1]


def _template(c, d, yaw, angle):
    """生成双侧偏置折线，左右按行驶方向定义，不按像素左右排序。

    返回投影网格采样／局部中心路线／转向候选。所有模板在启动时预计算，
    运行时只做灰度网格查表，避免在每帧搜索中重复三角函数和大数组。
    """
    u = math.sin(yaw), math.cos(yaw)
    v = math.sin(yaw+angle), math.cos(yaw+angle)
    cx, cz = c*u[1]+d*u[0], -c*u[0]+d*u[1]
    na, nb = (u[1], -u[0]), (v[1], -v[0])
    denominator = 1+u[0]*v[0]+u[1]*v[1]
    ox, oz = (na[0]+nb[0])*25/denominator, (na[1]+nb[1])*25/denominator
    ta = min(0., -cx*u[0]-cz*u[1])
    tb = max(0., -cx*v[0]-cz*v[1])
    pa, pb = _point(cx, cz, u, v, ta), _point(cx, cz, u, v, tb)
    nearest = ta if pa[0]*pa[0]+pa[1]*pa[1] <= pb[0]*pb[0]+pb[1]*pb[1] else tb
    origin = _point(cx, cz, u, v, nearest)
    if origin[0]*origin[0]+origin[1]*origin[1] > 24*24:
        return None
    sides = []
    for sign in (-1, 1):
        cells = set()
        for s in range(-120, 145, 6):
            x,z = _point(cx, cz, u, v, s)
            p = _pixel(x+sign*ox, z+sign*oz)
            if p is not None:
                cells.add(p)
        sides.append(array('H', sorted(cells)))
    if max(len(sides[0]),len(sides[1])) < 9:
        return None
    centers = []
    route = []
    for distance in (8, 16, 24, 32, 40, 48, 56):
        p = _point(cx, cz, u, v, nearest+distance)
        route.append(p)
        index = _pixel(*p)
        if index is not None:
            centers.append(index)
    target = route[3]
    steering = max(-1000, min(1000, round(math.atan2(target[0], max(5., target[1]))/math.radians(55)*1000)))
    return sides, array('H', centers), route, steering, (cx,cz,yaw,angle), (c,d,yaw,angle)


def _threshold(pixels):
    """稀疏大津阈值，按现有黑白场景加灰度上限；光照泛化待现场核验。"""
    hist = [0]*256
    for y in range(60,220,8):
        for x in range(4,316,8):
            hist[pixels[y*WIDTH+x]] += 1
    total=sum(hist); value=sum(i*n for i,n in enumerate(hist))
    n0=s0=0; best=-1.; threshold=40
    for i,n in enumerate(hist):
        n0+=n; s0+=i*n; n1=total-n0
        if n0 and n1:
            score=(s0/n0-(value-s0)/n1)**2*n0*n1
            if score>best:
                best=score; threshold=i
    return max(20,min(100,threshold))


def _grid(pixels, threshold):
    """每网格内取4个灰度样本；至少2个黑才标黑，减少JPEG孤点。

    当前组件以8邻域关联，最小3格；既允许连续带也保留分离小色块。
    膨胀一格仅容许采样误差，不把分离两侧当同一组件；标签只用于拒绝
    同一黑带两面被误当双边。标签不是边界语义真值。
    """
    # CanMV v1.8-0实板不支持array乘整数；先建立有界零列表再构造H数组。
    # 临时列表最多4800项，避免为了填零依赖桌面Python的array.__mul__。
    black=bytearray(GW*GH); labels=array('H',[0]*(GW*GH))
    for gy in range(GY0,GY1):
        y=gy*GRID_STEP
        for gx in range(1,GW-1):
            x=gx*GRID_STEP; p=y*WIDTH+x
            black[gy*GW+gx]=int((int(pixels[p]<=threshold)+int(pixels[p+2]<=threshold)+
                int(pixels[p+2*WIDTH]<=threshold)+int(pixels[p+2*WIDTH+2]<=threshold))>=2)
    component=0
    for start in range(GY0*GW,GY1*GW):
        if not black[start] or labels[start]:
            continue
        component+=1; labels[start]=component; queue=[start]; at=0
        minx=maxx=start%GW; miny=maxy=start//GW
        while at<len(queue):
            index=queue[at]; at+=1; x=index%GW; y=index//GW
            minx=min(minx,x); maxx=max(maxx,x); miny=min(miny,y); maxy=max(maxy,y)
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nx,ny=x+dx,y+dy
                    if not (0<=nx<GW and GY0<=ny<GY1):
                        continue
                    ni=ny*GW+nx
                    if black[ni] and not labels[ni]:
                        labels[ni]=component; queue.append(ni)
        # 拒绝极小噪点及ROI上沿实际横跨较宽区域的厚背景，单位均为网格。
        # 不能用整个组件的横向包围盒宽度判断“宽厚”：真实斜线从远到近
        # 横跨很多列，但每一行仍很窄。旧判断会在已保存的左右偏航原图
        # 中误删一侧完整边界，导致双边参照为空、车辆无法取得有效路径。
        # 仅在组件接触ROI上沿时数该行真实黑格，不增加／补画任何像素；
        # 面积门槛及后续白走廊、分离组件、模板支持、连续双帧保护都保留。
        # 额外计数只对接触上沿的组件做一次有界遍历，不执行完整模板搜索。
        top_cells=sum(1 for index in queue if index//GW==GY0) if miny==GY0 else 0
        if len(queue)<3 or (top_cells>120//GRID_STEP and len(queue)>4000//(GRID_STEP*GRID_STEP)):
            for index in queue:
                black[index]=0
    expanded=bytearray(GW*GH); near_labels=array('H',[0]*(GW*GH))
    for index in range(GY0*GW,GY1*GW):
        if not black[index]:
            continue
        x=index%GW; y=index//GW
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if 0<=x+dx<GW and 0<=y+dy<GH:
                    ni=index+dy*GW+dx; expanded[ni]=1
                    if not near_labels[ni]:
                        near_labels[ni]=labels[index]
    return black,expanded,near_labels


def _pair_anchors(black):
    """当前多行的双边白色走廊参照，仅用于约束模板与首次启动。

    候选宽度容许平面假设／姿态误差，但必须有两条分离黑段和白内侧。
    锐角仅一条横带时通常没有此参照；不把同一横带的两面当双边。
    行搜索是局部几何检查，不提供文字／真实道路的语义证明。
    """
    anchors=[]
    for gy in range((72+GRID_STEP-1)//GRID_STEP,216//GRID_STEP+1,2):
        runs=[]; start=None
        for gx in range(GW):
            dark=bool(black[gy*GW+gx])
            if dark and start is None: start=gx
            if not dark and start is not None:
                if 1<=gx-start<=56//GRID_STEP: runs.append((start,gx-1))
                start=None
        if len(runs)>8: continue
        y=gy*GRID_STEP+(GRID_STEP-1)/2; expected=50*(y+38.11111111111108)/48
        pairs=[]
        for left in runs:
            for right in runs:
                lx,rx=left[1]*GRID_STEP+GRID_STEP/2,right[0]*GRID_STEP+GRID_STEP/2
                if not (0<rx-lx and .72*expected<=rx-lx<=1.5*expected): continue
                lo,hi=left[1]+1,right[0]
                if any(black[gy*GW+i] for i in range(lo,hi)): continue
                z=(7802.22222222222-15.555555555555546*y)/(y+38.11111111111108)
                x=((lx+rx)/2-159.5)*48/(y+38.11111111111108)
                pairs.append((x,z,y))
        if len(pairs)==1: anchors.append(pairs[0])
    # 分离的单行巧合不足以证明两侧走廊。
    if len(anchors)<3 or max(p[2] for p in anchors)-min(p[2] for p in anchors)<16:
        return []
    return anchors


def _anchor_distance(t,anchors):
    """参照点到模型两条有向中心射线的距离；不能用无限延长线穿过内角。"""
    cx,cz,yaw,angle=t[4]; u=(math.sin(yaw),math.cos(yaw)); v=(math.sin(yaw+angle),math.cos(yaw+angle))
    distances=[]
    for x,z,_ in anchors:
        dx,dz=x-cx,z-cz
        a=min(0.,dx*u[0]+dz*u[1]); b=max(0.,dx*v[0]+dz*v[1])
        distances.append(min(_hypot(dx-a*u[0],dz-a*u[1]),_hypot(dx-b*v[0],dz-b*v[1])))
    return sum(distances)/len(distances) if distances else 0


# BEGIN lap_protocol.py
"""LowSpeedLap独立v2封包，原v1模块保持；无导入时串口副作用。

v2 error是局部推荐转向量，非固定y120偏差；bit2明确历史来源。
只编码／发送，不自动START。处理>100ms、总年龄>=150ms或未明确开启
drive许可时发新序号无效包；STOP用于脚本清理，不能充作车轮停稳证据。
"""
try:
    import ustruct as struct
except ImportError:
    import struct


class LapSender:
    def __init__(self,writer=None,allow_drive=False):
        self.writer=writer; self.allow_drive=allow_drive; self.seq=0; self.cmd_seq=0

    def _send(self,data):
        if self.writer is not None:
            offset=0
            while offset<len(data):
                written=self.writer(data[offset:])
                if not isinstance(written,int) or written<=0 or written>len(data)-offset:
                    raise OSError('UART short write failed; STM32 timeout must remain enabled')
                offset+=written
        return data

    def path(self,result,processing_ms,age_ms):
        if not isinstance(processing_ms,int) or not isinstance(age_ms,int) or processing_ms<0 or age_ms<0:
            raise ValueError('explicit nonnegative integer processing and acquisition age required')
        history=result.get('source')=='history'
        # history的年龄必须从最后有当前支持的模型算起，不能被空白新帧刷新。
        # 未提供证据年龄时默认过期；接收端也按120ms而非200ms执行监督。
        evidence_age=result.get('evidence_age_ms',120) if history else 0
        if not isinstance(evidence_age,int) or evidence_age<0:
            raise ValueError('known nonnegative model evidence age required')
        total_age=age_ms+evidence_age
        valid=bool(self.allow_drive and result.get('valid') and processing_ms<=100 and
                   total_age<(120 if history else 150))
        steering=int(result.get('steering',0)) if valid else 0
        bend=int(result.get('bend',0)) if valid else 0
        quality=int(result.get('confidence',0)) if valid else 0
        if not (-1000<=steering<=1000 and 0<=bend<=1000 and 0<=quality<=100):
            raise ValueError('invalid L1 local route fields')
        flags=int(valid)|(4 if valid and result.get('source')=='history' else 0)|(
            8 if valid and result.get('source')=='current_single_associated' else 0)
        header=bytes((0xa5,0x5a,2,1,12,self.seq)); self.seq=(self.seq+1)&255
        data=header+struct.pack('<BBhHHHBB',flags,quality,steering,min(total_age,1000),bend,min(processing_ms,1000),0,0)
        return self._send(data+struct.pack('<H',crc16(data)))

    def stop(self):
        header=bytes((0xa5,0x5a,2,2,12,self.cmd_seq)); self.cmd_seq=(self.cmd_seq+1)&255
        data=header+bytes(10)+bytes((2,0))
        return self._send(data+struct.pack('<H',crc16(data)))


def send_voice_start(sender, path_packet):
    """发送一次与刚发PATH序号绑定的Go。调用者先检查当前路径可用于起步。"""
    if not sender.allow_drive or not path_packet[6] & 1:
        raise ValueError('START requires a valid current PATH')
    data = bytes((0xa5, 0x5a, sender.wire_version, 2, 12, sender.cmd_seq,
                  0, 0, path_packet[5], 0, 0, 0, 0, 0, 0, 0, 1, 0))
    sender.cmd_seq = (sender.cmd_seq + 1) & 255
    return sender._send(data + struct.pack('<H', crc16(data)))

# BEGIN right_angle_racing.py
"""从T2二维折角生成外入、切弯、外出的圆弧候选，不强制沿道路中线。

几何沿用T2的入／出射线及法向偏置，移除桌面NumPy/OpenCV依赖。
单位均为现有投影代理单位，30半径／5偏置／14轮距是待实跑细调参数，
不能称全图厘米标定或已经证明车辆包络不触线。只在当前边界有支持时调用。
"""
import math

RACING_RADIUS = 30.0
RACING_OUTSET = 5.0
RACING_TRACK = 14.0  # 名义控制轮距代理量；未归档实测，不当作硬件尺寸事实。
JOINT_OUTSET = 2.0  # 两弯共用的外偏；首弯 v9 为 5，视频出弯已偏近外侧黑边。
JOINT_CLEARANCE = 21.0  # 名义线路到边界的最小代理距离，给车身半对角和跟踪误差留量。


def joint_racing_route(parameters):
    """连接任意正角度右弯的同偏置入口／出口。参数和输出距离均为地面投影代理量。

    以模型车道宽50计算余量：外侧由共同偏置约束，最靠近内角处在圆弧中点。
    根据该处到内侧折点的距离限制半径；用同一个偏置衔接首弯出口和次弯入口。
    返回车头投影最近点、弧后的有符号纵向进度和前视路线，供控速、续行和退出使用。
    """
    cx, cz, yaw, angle = parameters
    half = angle / 2
    secant = 1 / math.cos(half)
    radius_limit = ((25 + JOINT_OUTSET) * secant - JOINT_CLEARANCE) / (secant - 1)
    radius = min(30.0 if angle > 1 else 58.0, radius_limit)
    u, n = (math.sin(yaw), math.cos(yaw)), (math.cos(yaw), -math.sin(yaw))
    va, vz = math.sin(angle), math.cos(angle)
    tangent = -(radius - JOINT_OUTSET) * math.tan(half)
    center_x = radius - JOINT_OUTSET
    end_x = center_x - radius * vz
    end_z = tangent + radius * va
    arc_length = radius * angle
    qx, qz = -cx*n[0]-cz*n[1], -cx*u[0]-cz*u[1]
    arc_theta = max(0.0, min(angle, math.atan2(qz - tangent, center_x - qx)))
    exit_s = (qx - end_x) * va + (qz - end_z) * vz

    def point(s):
        if s <= 0:
            return -JOINT_OUTSET, tangent + s
        if s < arc_length:
            theta = s / radius
            return center_x - radius*math.cos(theta), tangent + radius*math.sin(theta)
        return end_x + (s - arc_length)*va, end_z + (s - arc_length)*vz

    def distance2(s):
        x, z = point(s)
        return (x - qx)**2 + (z - qz)**2

    along = min((min(0.0, qz - tangent), radius * arc_theta,
                 arc_length + max(0.0, exit_s)), key=distance2)
    route = []
    for ahead in (8, 16, 24, 32, 40, 48, 56):
        x, z = point(along + ahead)
        route.append((cx+x*n[0]+z*u[0], cz+x*n[1]+z*u[1]))
    x, z = route[2]
    ratio = RACING_TRACK*x/max(25.0, x*x+z*z)
    return dict(route=route, steering=round(max(-0.65, min(0.65, ratio))*1000), radius=radius,
                outset=JOINT_OUTSET, phase='entry' if along < 0 else ('arc' if along < arc_length else 'exit'),
                projection_s=along, entry_distance=max(0.0, -along), exit_s=exit_s)


def _racing_point(distance, radius, outset):
    """按连续弧长返回局部路线点(x,z)，坐标及弧长均为投影代理单位。

    distance=0是入弯直线与圆弧的切点；负值在入口直道，正值先走圆弧，
    超过四分之一圆周后进入出口直道。三个区间位置／切向连续，不按离散
    点号跳转，也不把相机看到角点等同于车辆已经到达入弯点。
    """
    tangent = outset-radius
    arc_length = radius*math.pi/2
    if distance < 0:
        return -outset, tangent+distance
    if distance <= arc_length:
        angle = distance/radius
        return radius-outset-radius*math.cos(angle), tangent+radius*math.sin(angle)
    return radius-outset+distance-arc_length, outset


def racing_route(parameters, include_nominal=True):
    """返回当前模型的推荐线、差速请求及圆弧曲率，右正。

    parameters=(cx,cz,yaw,angle)来自当前观测模板；先外侧准备，再用圆弧
    连接两条路段。先把车头原点投影到入口直线／圆弧／出口直线，取真正
    最近点的连续弧长，再前视24代理单位。避免旧离散最近点带来的4单位
    跳动，更不使用角点纵距55..15强制施加30%..65%右转。
    返回路线、差速千分比、最近点阶段及距离；差速比≈轮距*x/(x²+z²)。
    左右符号由当前路线决定；只有调用方已确认的当前路径才能授予许可。
    不使用KEY后的累计时间，未知角度返回None，几何仍未标定为实际厘米。
    """
    cx,cz,yaw,angle = parameters
    if abs(angle-math.pi/2) > 0.01:
        return None
    u=(math.sin(yaw),math.cos(yaw)); n=(u[1],-u[0])
    radius=RACING_RADIUS; offset=RACING_OUTSET
    # 车辆原点在入弯道路局部坐标中的位置。比较三段的最近候选，不能仅
    # 根据角点在相机坐标中的cz判断何时转弯；车头已经偏转时cz尤其不足。
    qx = -cx*n[0]-cz*n[1]
    qz = -cx*u[0]-cz*u[1]
    tangent=offset-radius
    arc_length=radius*math.pi/2
    angle_on_arc=max(0.0,min(math.pi/2,math.atan2(qz-tangent,radius-offset-qx)))
    choices=((min(0.0,qz-tangent),(-offset,min(qz,tangent))),
             (radius*angle_on_arc,(radius-offset-radius*math.cos(angle_on_arc),
                                   tangent+radius*math.sin(angle_on_arc))),
             (arc_length+max(0.0,qx-(radius-offset)),(max(qx,radius-offset),offset)))
    nearest_distance, _ = min(choices,key=lambda item:(item[1][0]-qx)**2+(item[1][1]-qz)**2)
    phase='entry' if nearest_distance<0 else ('arc' if nearest_distance<arc_length else 'exit')
    route=[]
    for ahead in (8,16,24,32,40,48,56):
        x,z=_racing_point(nearest_distance+ahead,radius,offset)
        route.append((cx+x*n[0]+z*u[0],cz+x*n[1]+z*u[1]))
    # 完整名义线只用于离线图示／包络检查，车载逐帧计算直接使用上方7点。
    points=[]
    if include_nominal:
        local=[]
        for along in range(-140,int(tangent),4):
            local.append((-offset,float(along)))
        for degree in range(0,91,5):
            a=math.radians(degree)
            local.append((radius-offset-radius*math.cos(a),offset-radius+radius*math.sin(a)))
        for along in range(int(radius-offset)+4,146,4):
            local.append((float(along),offset))
        points=[(cx+x*n[0]+z*u[0],cz+x*n[1]+z*u[1]) for x,z in local]
    x,z=route[2]
    ratio=RACING_TRACK*x/max(25.0,x*x+z*z)
    ratio=max(-0.65,min(0.65,ratio))
    return dict(route=route,nominal_path=points,steering=int(round(ratio*1000)),radius=radius,
                outset=offset,lookahead=24,geometry_calibrated=False,phase=phase,
                projection_s=nearest_distance,entry_distance=max(0.0,-nearest_distance),
                exit_s=qx-(radius-offset))

# BEGIN right_angle_grid.py
"""首弯网格：只剥离上沿厚背景，保留与背景偶然接触的细长赛道边。

沿用既有6像素采样／组件／一格容差，不改直道或旧整圈模块的_grid。
修复实图run_0007_loss_03：ROI黑墙与L形边界连接后，旧版删除整个组件，
真实左边和前横边同时变成0。新版本只删上沿连通的厚核及一格外扩。
"""
from array import array


def _peel_background(black, component):
    """从ROI上沿的3x3实黑厚核出发，只删除厚背景本体。

    细长黑边即便与墙有单格连接，也不能把整条边升级为厚背景；其余位置
    的厚核（例如近处较宽的胶带）不靠细桥连到上沿厚核，不会跟着被删除。
    不制造任何新黑像素；原始PGM和去背景黑格分开，可复现真实支持。
    """
    core=set()
    for index in component:
        x=index%GW; y=index//GW
        if not (1<=x<GW-1 and GY0<y<GY1-1):continue
        if all(black[index+dy*GW+dx] for dy in (-1,0,1) for dx in (-1,0,1)):
            core.add(index)
    queue=[index for index in core if index//GW<=GY0+2]
    wall=set(queue);at=0
    while at<len(queue):
        index=queue[at];at+=1
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                other=index+dy*GW+dx
                if other in core and other not in wall:
                    wall.add(other);queue.append(other)
    for index in component:
        if any(index+dy*GW+dx in wall for dy in (-1,0,1) for dx in (-1,0,1)):
            black[index]=0


def sample_black_rows(pixels, threshold, rows):
    """按指定网格行采样灰度，用于近中区快速走廊和完整弯道组件的共同入口。"""
    black = bytearray(GW*GH)
    for gy in rows:
        for gx in range(1,GW-1):
            p=gy*GRID_STEP*320+gx*GRID_STEP
            black[gy*GW+gx]=int((int(pixels[p]<=threshold)+int(pixels[p+2]<=threshold)+
                int(pixels[p+640]<=threshold)+int(pixels[p+642]<=threshold))>=2)
    return black


def corner_grid(pixels, threshold):
    """输入320x240灰度及阈值，返回当前黑格／容差网格／组件标签。

    4点至少2黑才采黑；小于3格的噪声组件仍拒绝。一格扩张只用于模型
    采样容差，不充作真实黑边。所有容器大小受320x240网格固定上界限制。
    """
    black=sample_black_rows(pixels, threshold, range(GY0,GY1));labels=array('H',[0]*(GW*GH))
    number=0
    for start in range(GY0*GW,GY1*GW):
        if not black[start] or labels[start]:continue
        number+=1;labels[start]=number;queue=[start];at=0;top=0
        while at<len(queue):
            index=queue[at];at+=1;x=index%GW;y=index//GW
            if y==GY0:top+=1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nx=x+dx;ny=y+dy
                    if not (0<=nx<GW and GY0<=ny<GY1):continue
                    other=ny*GW+nx
                    if black[other] and not labels[other]:
                        labels[other]=number;queue.append(other)
        if len(queue)<3:
            for index in queue:black[index]=0
        elif top>120//GRID_STEP and len(queue)>4000//(GRID_STEP*GRID_STEP):
            _peel_background(black,queue)
    expanded=bytearray(GW*GH);near_labels=array('H',[0]*(GW*GH))
    for index in range(GY0*GW,GY1*GW):
        if not black[index]:continue
        x=index%GW;y=index//GW
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if 0<=x+dx<GW and 0<=y+dy<GH:
                    other=index+dy*GW+dx;expanded[other]=1
                    if not near_labels[other]:near_labels[other]=labels[index]
    return black,expanded,near_labels

# BEGIN right_angle_prediction.py
"""从当前灰度网格重估首弯外边；坐标沿用现有地面投影代理单位。"""
import math

# 持续单侧证据和瞬时白走廊的上限分别核对；低置信度帧不能续租强观测。
PREDICTION_ANCHOR_MS = 1200
PREDICTION_GAP_MS = 240
STRAIGHT_CONTROL_ROWS = range((72 + GRID_STEP - 1) // GRID_STEP, 216 // GRID_STEP + 1, 2)


def turn_ahead(pixels, threshold, reference):
    """远区用少量投影格找进入前方白区的黑边；只触发备选搜索，不发转向命令。

    42到90是前向投影代理量。横向取距旧中线-17到+10的内部位置，跳过原边界。
    两个不同实黑格才有预警。角度和弯心继续由弯道两臂的当前实测确定。
    """
    cx, cz, u_x, u_z, _, _ = reference[7]
    base = cx*u_z - cz*u_x
    dark = set()
    for forward in (42, 48, 54, 62, 70, 80, 90):
        for lateral in (-17, -11, -5, 2, 10):
            cross = base + lateral
            cell = _pixel(forward*u_x + cross*u_z, forward*u_z - cross*u_x)
            if cell is None or cell in dark:
                continue
            x, y = cell % GW * GRID_STEP, cell // GW * GRID_STEP
            at = y*320+x
            if sum(pixels[at+delta] <= threshold for delta in (0, 2, 640, 642)) >= 2:
                dark.add(cell)
                if len(dark) >= 2:
                    return True
    return False


def _project_row(gy):
    y = gy * GRID_STEP + 1
    return ((7802.22222222222 - 15.555555555555546 * y) / (y + 38.11111111111108),
            48.0 / (y + 38.11111111111108))


def _left_rail(black, right=False):
    """在近区多行找细黑边与它右侧的白区，拟合车道左边直线。

    使用未扩张黑格求中心；平行背景或断裂噪声不能用一个采样点参与拟合。
    返回行驶方向、法向偏移和最远实测投影。right为真时从右边向内搜索。
    单靠此结果不会确认新弯，左右边线均使用真实像素坐标和相同的白侧检查。
    """
    samples = []
    rows = range((108 + GRID_STEP - 1) // GRID_STEP, 216 // GRID_STEP, 18 // GRID_STEP)
    edge = GW - 1 if right else 0
    step = -1 if right else 1
    for gy in rows:
        base = gy * GW
        row = black[base:base + GW]
        start = None
        for gx in range(1, GW - 4):
            # 右边从物理列倒序走。CanMV v1.8 不支持 bytearray 的负步长切片。
            index = edge + step * gx
            if row[index]:
                if start is None:
                    start = gx
            elif start is not None:
                white_at = index - 3 if right else index
                if 2 <= gx - start <= 60 // GRID_STEP and not any(row[white_at:white_at + 4]):
                    z, scale = _project_row(gy)
                    middle = (start + gx - 1) / 2
                    if right:
                        middle = GW - 1 - middle
                    x = (middle * GRID_STEP + 1 - 159.5) * scale
                    samples.append((x, z))
                    break
                start = None
    if len(samples) < 4:
        return None
    dx, dz = samples[0][0] - samples[-1][0], samples[0][1] - samples[-1][1]
    length = math.sqrt(dx * dx + dz * dz)
    if length < 8:
        return None
    ux, uz = dx / length, dz / length
    yaw = math.atan2(ux, uz)
    offsets = [uz * x - ux * z for x, z in samples]
    offset = sum(offsets) / len(offsets)
    inward_offset, inward_yaw = (-offset, -yaw) if right else (offset, yaw)
    if not (-48 <= inward_offset <= -8 and -1.3 <= inward_yaw <= 0.44 and max(offsets) - min(offsets) <= 4):
        return None
    return ux, uz, yaw, offset, max(ux * x + uz * z for x, z in samples)


def fitted_outer_l(black, occupied, template, angle=math.pi / 2):
    """用左外边两臂的当前像素求交，返回指定右转角的已验证模板或None。

    横边沿左边方向的投影应近似等长，按4代理单位归桶。用不同横向
    区段计票，并验证实际连接处、两臂覆盖和内侧白区。网格和候选数有界。
    """
    rail = _left_rail(black)
    if rail is None:
        return None
    ux, uz, yaw, offset, last = rail
    right_angle = angle > 1
    slope = 0 if right_angle else math.cos(angle) / math.sin(angle)
    start_margin = 5 if right_angle else -4
    votes = {}
    first_row = max(GY0 + 3, (60 + GRID_STEP - 1) // GRID_STEP)
    for gy in range(first_row, min(GY1, 162 // GRID_STEP)):
        base = gy * GW
        z, scale = _project_row(gy)
        for gx in range(1, GW - 1):
            if not black[base + gx]:
                continue
            x = (gx * GRID_STEP + 1 - 159.5) * scale
            lateral = uz * x - ux * z - offset
            # 钝角处的出弯臂沿来向仍有前进分量，扣掉后才得到两臂的交点纵距。
            along = ux * x + uz * z - lateral * slope
            if 8 <= lateral <= 85 and start_margin <= along - last <= 90:
                key = round(along / 4)
                votes[key] = votes.get(key, 0) | (1 << int(lateral / 5))
    # 每个桶最多17个横向区段；用定宽掩码，避免为每个黑格分配集合。
    ranked = [(bin(mask).count('1'), key) for key, mask in votes.items()]
    ranked.sort(reverse=True)
    for support, key in ranked[:3]:
        if support < (6 if right_angle else 4):
            break
        along = key * 4
        join = _pixel(offset * uz + along * ux, -offset * ux + along * uz)
        if join is None or not occupied[join]:
            continue
        candidate = template(offset + 25, along - (25 if right_angle else 25 * math.tan(angle / 2)), yaw, angle)
        if candidate is None:
            continue
        arms = candidate[6][:2]
        if (all(len(arm) >= 3 and sum(occupied[i] for i in arm) >= 0.70 * len(arm) for arm in arms)
                and len(candidate[8]) >= 4 and sum(black[i] for i in candidate[8]) <= len(candidate[8]) // 5
                and not any(black[i] for i in candidate[1])):
            return candidate
    return None


def fitted_left_forecast(black, previous, template):
    """只见左边时重估横向偏差和朝向，沿用最近模型的弯点纵向位置。

    当前纵边无法单独推断前方弯点，因此仅用于短程预测，不能续租双边/L形。
    """
    rail = _left_rail(black)
    if rail is None:
        return None
    ux, uz, yaw, offset, _ = rail
    cx, cz, _, angle = previous[4]
    return template(offset + 25, cx * ux + cz * uz, yaw, angle)


def fitted_straight_rail(black, previous, template):
    """按当前单侧多行像素更新已知直道中线。只沿用原车道侧别，不估算新弯心。

    直道模型的横向截距和偏航来自当前画面。车道宽50和截距门限沿用投影代理量。
    单根黑线必须和旧走廊的位置／方向一致，且由调用方复核前方白色推荐线。
    """
    old_offset, _, old_yaw, _ = previous[5]
    best = None
    best_error = 16.0
    for right in (False, True):
        rail = _left_rail(black, right)
        if rail is None:
            continue
        _, _, yaw, offset, _ = rail
        center = offset - 25 if right else offset + 25
        angle_error = abs(yaw - old_yaw)
        if abs(center - old_offset) > 10 or angle_error > math.radians(16):
            continue
        error = abs(center - old_offset) + angle_error * 24
        if error < best_error:
            candidate = template(center, 50, yaw, 0)
            if candidate is not None:
                best, best_error = candidate, error
    return best


def fitted_front_edge(black, previous, template):
    """已知右弯后，沿预期前横线的法向取样，逐帧重估前线距离和角度。

    单条线约束方向和法向距离。弯心沿线坐标沿用上次模型，直到新双侧可见。
    采样只看当前未扩张黑格，隔开墙面上沿；输出代理坐标与实测格数。
    """
    cx, cz, yaw, angle = previous[4]
    # 在出弯坐标里，原前边始终是左边。直角和钝角只相差出弯方向的旋转量。
    heading = yaw + angle
    ux, uz = math.sin(heading), math.cos(heading)
    across_center = cx * ux + cz * uz
    depth = -(cx * uz - cz * ux) + 25
    samples = []
    used = set()
    across_start = across_center + 25 * math.tan(angle / 2)
    for across in range(round(across_start) - 42, round(across_start) + 36, 7):
        for shift in (0, -3, 3, -6, 6, -9, 9, -12, 12, -15, 15):
            forward = depth + shift
            cell = _pixel(across * ux - forward * uz, across * uz + forward * ux)
            if cell is None or cell // GW < GY0 + 3 or not black[cell]:
                continue
            if cell not in used:
                used.add(cell)
                samples.append((across, forward))
            break
    if len(samples) < 5 or samples[-1][0] - samples[0][0] < 28:
        return None
    mean_across = sum(p[0] for p in samples) / len(samples)
    mean_depth = sum(p[1] for p in samples) / len(samples)
    variance = sum((p[0] - mean_across) ** 2 for p in samples)
    slope = sum((p[0] - mean_across) * (p[1] - mean_depth) for p in samples) / variance
    if abs(slope) > 0.45 or max(abs(z - mean_depth - slope * (x - mean_across)) for x, z in samples) > 6:
        return None
    change = -math.atan(slope)
    updated_yaw = yaw + change
    if not -math.radians(105) <= updated_yaw <= math.radians(30):
        return None
    front = mean_depth * math.cos(change) + mean_across * math.sin(change)
    heading += change
    ux, uz = math.sin(heading), math.cos(heading)
    across_center = cx * ux + cz * uz
    x, z = across_center * ux + (25 - front) * uz, across_center * uz - (25 - front) * ux
    a, b = math.sin(updated_yaw), math.cos(updated_yaw)
    candidate = template(x * b - z * a, x * a + z * b, updated_yaw, angle)
    if candidate is None:
        return None
    return candidate, len(samples), front


def clear_predicted_corridor(pixels, black, threshold, route, minimum=3):
    """检查最靠近车的四个可见路线格，相机近端盲区的不计入。"""
    cells = set()
    for point in route:
        cell = _pixel(*point)
        if cell is None or cell in cells:
            continue
        x, y = cell % GW * GRID_STEP + 1, cell // GW * GRID_STEP + 1
        if black[cell] or pixels[y * 320 + x] <= threshold:
            return False
        cells.add(cell)
        if len(cells) == 4:
            return True
    return len(cells) >= minimum

# BEGIN straight_route.py
"""直道专用观测器：只读当前双边，不搜索转弯模板、不沿用历史路径。

输入固定320x240灰度字节。复用现有黑块采样／双边白走廊检查，使用
已有近似投影只计算纠偏代理量；输出不是经过完整标定的厘米或航向。
无导入时相机／UART副作用，可在电脑和CanMV执行同一核心。
"""


class StraightRoute:
    """每帧只拟合一条直道，至少三帧／80ms一致后才许可。

    横向项使车回到道路中央，斜率项使车头顺道路方向；不能仅用横向
    偏差等到压线再纠正。增益与几何门槛为现场待验候选。
    """
    def __init__(self):
        self.reset()

    def reset(self):
        """失线、异常时间或几何跳变后撤销连续许可，没有历史续跑。"""
        self.last_at = None
        self.previous_error = None
        self.stable = 0
        self.stable_at = 0

    @staticmethod
    def command(near, slope):
        """沿用直道横偏和方向权重，返回右正的归一化纠偏量。"""
        return max(-1.0, min(1.0, 0.7 * near / 25.0 + 1.2 * slope))

    def update(self, pixels, now):
        """now为本次取图开始的相对毫秒；返回原始误差及拒绝原因。

        无效帧也必须发送新序号无效包，不能只停止打印或重复上一有效包。
        近似坐标的30／50参照必须处于当前真实支持范围内；直道弯折或
        靠边超出微调能力时撤许可，绝不把直线外推穿过锐角。
        """
        result = dict(valid=False, source='unknown', steering=0, bend=0,
                      confidence=0, support=0, reason='no_pair')
        if len(pixels) != 320 * 240 or not isinstance(now, int) or now < 0:
            self.reset()
            result['reason'] = 'input'
            return result
        threshold = _threshold(pixels)
        black, _, _ = _grid(pixels, threshold)
        return self.update_anchors(_pair_anchors(black), now, threshold)

    def update_anchors(self, points, now, threshold):
        """联合版复用本直道拟合和稳定门，使用同一帧已经算出的双边走廊参照。"""
        result = dict(valid=False, source='unknown', steering=0, bend=0,
                      confidence=0, support=len(points), reason='no_pair', threshold=threshold)
        timing_ok = self.last_at is None or 0 < now - self.last_at <= 150
        if not timing_ok:
            self.reset()
        self.last_at = now
        if len(points) < 8:
            self.stable = 0
            self.previous_error = None
            return result
        count = len(points)
        mx = sum(p[0] for p in points) / count
        mz = sum(p[1] for p in points) / count
        low = min(p[1] for p in points)
        high = max(p[1] for p in points)
        denominator = sum((p[1] - mz) ** 2 for p in points)
        slope = sum((p[1] - mz) * (p[0] - mx) for p in points) / max(0.001, denominator)
        near = mx + slope * (30 - mz)
        far = mx + slope * (50 - mz)
        residual = (sum((p[0] - mx - slope * (p[1] - mz)) ** 2 for p in points) / count) ** 0.5
        # 只比较短半段斜率会把6像素网格的一格跳变放大成假折角：
        # 2026-11-18地面第1961帧支持13行、整体残差0.475却因斜率差>0.12停车。
        # 改为比较斜率变化在实际支持跨度内形成的横向弯折量，并限制单点残差。
        # 所有量沿用近似投影代理单位，不冒称已标定厘米；缺半段／跨度不足仍拒绝。
        slopes = []
        half_spans = []
        for half in ([p for p in points if p[1] <= mz], [p for p in points if p[1] > mz]):
            if len(half) < 3:
                continue
            hx = sum(p[0] for p in half) / len(half)
            hz = sum(p[1] for p in half) / len(half)
            den = sum((p[1] - hz) ** 2 for p in half)
            slopes.append(sum((p[1] - hz) * (p[0] - hx) for p in half) / max(0.001, den))
            half_spans.append(max(p[1] for p in half) - min(p[1] for p in half))
        max_residual = max(abs(p[0] - mx - slope * (p[1] - mz)) for p in points)
        slope_delta = abs(slopes[0] - slopes[1]) if len(slopes) == 2 else None
        # 等长V形折线对整段直线的最大偏离约为斜率差×半跨度/4；
        # 这里用该有界几何量筛折角，避免无量纲斜率误差与实际观测长度脱节。
        deflection = slope_delta * min(half_spans) / 4 if slope_delta is not None else None
        result.update(half_slope_delta=slope_delta, bend_deflection=deflection,
                      max_residual=max_residual, half_depth_spans=half_spans)
        result.update(near_error=near, far_error=far, heading_proxy=slope,
                      residual=residual, depth_min=low, depth_max=high)
        gates = (('depth_coverage', low <= 30 and high >= 50 and high - low >= 25),
                 ('position', abs(near) <= 12 and abs(far) <= 18),
                 ('heading', abs(slope) <= 0.35), ('global_fit', residual <= 1.2),
                 ('single_point_fit', max_residual <= 1.8),
                 ('two_halves', len(slopes) == 2 and min(half_spans) >= 8),
                 ('bend_displacement', deflection is not None and deflection <= 1.5))
        failures = [name for name, passed in gates if not passed]
        result['geometry_failures'] = failures
        if failures:
            self.stable = 0
            self.previous_error = None
            result['reason'] = 'outside_straight_envelope'
            return result
        error = self.command(near, slope)
        if self.previous_error is None or abs(error - self.previous_error) > 0.22 or not timing_ok:
            self.stable = 1
            self.stable_at = now
        else:
            self.stable += 1
        self.previous_error = error
        result.update(valid=self.stable >= 3 and now - self.stable_at >= 80,
                      source='current_pair', steering=int(round(error * 1000)),
                      confidence=80, reason='ready' if self.stable >= 3 and now - self.stable_at >= 80 else 'stabilizing')
        return result

# BEGIN right_angle_route.py
"""首个直角弯：只搜索直道与顺时针90度右弯，不按时间排定转弯。

320x240灰度输入，复用既有近似地面投影／网格／黑块组件。每帧重新
检查黑边、白走廊及局部路线关联。上一模型只缩小搜索范围，不能
代替当前像素支持；当前左纵／前横L可独立预测右转，普通单直边不能启动。
投影仍是候选代理坐标，不能把模板宽度当作实测车体余量。
"""
import math

OBTUSE_TURN = math.radians(39)  # 图1约141°内角对应车头右转约39°。


def _corner_template(c, d, yaw, angle):
    """附加两侧边界的入／出弯臂采样，单边许可必须实际看到折角两臂。

    不把一根直黑带或全无当前支持的旧模型称作单边转弯证据。
    采样使用与原模板一致的代理投影，未标定部分不生成真实厘米结论。
    """
    t = _template(c, d, yaw, angle)
    if t is None: return None
    cx, cz = t[4][:2]
    u = math.sin(yaw), math.cos(yaw)
    v = math.sin(yaw+angle), math.cos(yaw+angle)
    vectors = (cx, cz, u[0], u[1], v[0], v[1])
    if angle == 0:
        # 直道没有折角臂，不需要重复投影。
        return t+(((), (), (), ()), vectors, ())
    den = 1+u[0]*v[0]+u[1]*v[1]
    ox, oz = (u[1]+v[1])*25/den, (-u[0]-v[0])*25/den
    arms = []
    for sign in (-1, 1):
        for direction in (-1, 1):
            cells = set()
            for distance in (6,12,18,24,30,36,42):
                x, z = _point(cx, cz, u, v, direction*distance)
                cell = _pixel(x+sign*ox, z+sign*oz)
                if cell is not None: cells.add(cell)
            arms.append(tuple(cells))
    interior=set()
    for direction in (-1,1):
        normal=(u[1],-u[0]) if direction<0 else (v[1],-v[0])
        for distance in (6,12,18,24,30,36,42):
            x,z=_point(cx,cz,u,v,direction*distance)
            # 向内10代理单位取白区，避开黑带厚度和粗模板数格误差；不补造边界。
            cell=_pixel(x-ox+10*normal[0],z-oz+10*normal[1])
            if cell is not None:interior.add(cell)
    return t+(arms, vectors, tuple(interior))


def _current_anchor_distance(t, anchors):
    """与原双射线距离等价，复用模板方向，逐点只做一次sqrt。

    sqrt单调，因此min(sqrt(a),sqrt(b))等于sqrt(min(a,b))。
    不更改几何门槛或历史条件，避免每候选重复三角函数和中间列表分配。
    """
    cx, cz, ux, uz, vx, vz = t[7]
    total = 0.0
    for x,z,_ in anchors:
        dx = x-cx; dz = z-cz
        a = min(0.0, dx*ux+dz*uz); b = max(0.0, dx*vx+dz*vz)
        ax = dx-a*ux; az = dz-a*uz; bx = dx-b*vx; bz = dz-b*vz
        total += math.sqrt(min(ax*ax+az*az, bx*bx+bz*bz))
    return total/len(anchors) if anchors else 0.0


def _along_exit_edge(t, outset=0):
    """车头接近出弯方向时，把已跟踪的前线作为出口左边推算中线。"""
    cx, cz, yaw, angle = t[4]
    heading = yaw + angle
    if heading > math.radians(15):
        return None
    nx, nz = math.cos(heading), -math.sin(heading)
    offset = cx*nx + cz*nz - outset
    return [(offset*nx-ahead*nz, offset*nz+ahead*nx) for ahead in (8, 16, 24, 32, 40, 48, 56)]


def _same_rail(first, first_turn, second, second_turn=0):
    """用方向和法向截距判断相邻模型是否观测到同一条车道中线，距离为代理单位。"""
    ax, az, ayaw, _ = first[4]
    bx, bz, byaw, _ = second[4]
    ayaw += first_turn
    byaw += second_turn
    return (abs(ayaw - byaw) <= math.radians(24) and
            abs(ax*math.cos(ayaw) - az*math.sin(ayaw) -
                (bx*math.cos(byaw) - bz*math.sin(byaw))) <= 12)


def _corridor_blocked(black, route):
    """旧推荐线上两个不同的可见实黑投影格才确认受阻。"""
    cells = {_pixel(*point) for point in route}
    return sum(black[cell] for cell in cells if cell is not None) >= 2


def _straight_reference(t, racing):
    """给当前单边重拟合限定参考直段。圆弧中间仍由实测弯边或短预测负责。"""
    cx, cz, yaw, angle = t[4]
    if angle == 0:
        return t
    if racing['entry_distance'] >= 12:
        return _corner_template(t[5][0], 50, yaw, 0)
    heading = yaw + angle
    if racing['phase'] == 'exit' and abs(heading) <= math.radians(16):
        offset = cx*math.cos(heading) - cz*math.sin(heading)
        return _corner_template(offset, 50, heading, 0)
    return None


def _still_has_l(t, black, occupied):
    """复核上一候选的两条外臂和内侧白区，避免冷启动退成单边许可。"""
    if not -math.radians(85) <= t[4][2] <= math.radians(25):
        return False
    side = t[0][0]
    count = sum(occupied[cell] for cell in side)
    return (count >= 12 and count >= .75 * len(side) and len(t[8]) >= 4
            and sum(black[cell] for cell in t[8]) <= len(t[8]) // 5
            and not any(black[cell] for cell in t[1])
            and all(len(arm) >= 3 and sum(occupied[cell] for cell in arm) >= max(3, .65 * len(arm))
                    for arm in t[6][:2]))


class RightAngleRoute:
    """固定有界候选库与局部细化；初始化预计算只执行一次，不驱动车轮。"""
    def __init__(self, predictive=False, joint=False):
        self.predictive = predictive
        self.joint = joint
        self.outset = JOINT_OUTSET if joint else 0
        self.straight = StraightRoute() if joint else None
        self.clock = None  # 可选板上ticks_ms，只计耗时，不改变几何判断或源年龄。
        self.templates = []
        for angle in (0, 90):
            for yaw in ((-30, -15, 0, 15, 30) if angle == 0 else (-90, -60, -30, 0, 15)):
                for c in (-12, 0, 12):
                    for d in ((50,) if angle == 0 else (0, 10, 20, 40, 60, 80)):
                        t = _corner_template(c, d, math.radians(yaw), math.radians(angle))
                        if t is not None:
                            self.templates.append(t)
        self.obtuse_templates = []
        self.straight_templates = [t for t in self.templates if t[4][3] == 0]
        if joint:
            for yaw in (-45, -30, -15, 0, 15):
                for c in (-10, 0, 10):
                    for d in (0, 16, 34, 56, 80):
                        t = _corner_template(c, d, math.radians(yaw), OBTUSE_TURN)
                        if t is not None:
                            self.obtuse_templates.append(t)
        self.reset()

    def reset(self):
        """失线后不保存有效许可；重获必须重新满足3帧／80ms门槛。"""
        self.previous = None
        self.last_at = None
        self.stable = 0
        self.stable_at = 0
        self.search_cursor = 0
        self.neighbor_key = None
        self.neighbors = []
        self.recovery_key = None
        self.recoveries = []
        self.refine_key = None
        self.refinements = []
        self.corner_at = None
        self.forecast_anchor_at = self.visible_edge_at = None
        self.rail_at = None
        self.forecast_route = self.forecast_command = None
        self.front_model = self.front_at = None
        self.racing_key = None
        self.racing = None
        self.first_corner = False
        self.first_exit = None
        self.second_corner = False
        self.second_exit = None
        self.second_exit_at = None
        self.preview_at = None
        if self.straight is not None:
            self.straight.reset()

    def curve(self, parameters):
        """联合版和首弯版共用候选搜索及稳定确认，各自采用对应的控制线。"""
        if self.joint:
            if parameters[3] > 1:
                return racing_route(parameters, include_nominal=False)
            return joint_racing_route(parameters)
        return racing_route(parameters, include_nominal=not self.predictive)

    @staticmethod
    def distance(a, b):
        return sum(_hypot(a[2][i][0]-b[2][i][0], a[2][i][1]-b[2][i][1])
                   for i in (0, 2, 4))/3

    def _use_straight(self, result, reference, now):
        """采用旧直道解，更新实际走廊，供下一帧只见一侧时重新估计。"""
        near, slope = result['near_error'], result['heading_proxy']
        offset = self.outset / math.cos(reference[4][2])
        route = [(near + (z-30)*slope - offset, z) for z in (16, 24, 30, 38, 46, 54, 62)]
        steering = round(StraightRoute.command(near - offset, slope) * 1000)
        self.previous = reference
        self.stable, self.stable_at = self.straight.stable, self.straight.stable_at
        self.forecast_route, self.forecast_command = route, (steering, 0)
        self.forecast_anchor_at = self.visible_edge_at = now
        if self.first_exit is not None:
            self.first_exit = reference
        result.update(source='straight_pair', stage='straight', steering=steering, route=route,
                      road_section='connector' if self.first_exit else 'start_straight',
                      geometry_calibrated=False, parameters=reference[4], vision_mode='near_mid')
        return result

    def update(self, pixels, now):
        """now为取图开始的会话ms；任何拒绝均返回新无效观测，禁止沿用旧命令。

        双侧模式须不同组件支持同一个模型及当前白色路径。左纵／前横
        L单独确认时，只由当前外边两臂和朝道路内侧的白区预测缺失右边与
        圆弧；中线在近端盲区时仍可预测。出口单直边只允许700ms当前关联。
        同一横黑带不能借两面冒充两侧边界，历史／空白帧不能刷新许可。
        """
        out = dict(valid=False, source='unknown', steering=0, bend=0,
                   confidence=0, support=[0, 0], reason='no_current_pair',
                   stage='unknown', geometry_calibrated=False)
        if len(pixels) != 76800 or not isinstance(now, int) or now < 0:
            self.reset(); out['reason'] = 'input'; return out
        if self.last_at is not None and not 0 < now-self.last_at <= 150:
            self.reset()
        self.last_at = now
        clock = self.clock
        begun = clock() if clock else 0
        threshold = _threshold(pixels)
        straight = reference = None
        if self.joint and (not self.first_corner or self.first_exit is not None) and not self.second_corner:
            # 双边直道只扫旧算法实际使用的近／中区行，无需每帧做连通域或展开全部弯道模板。
            bands = sample_black_rows(pixels, threshold, STRAIGHT_CONTROL_ROWS)
            straight = self.straight.update_anchors(_pair_anchors(bands), now, threshold)
            if straight['valid']:
                slope = straight['heading_proxy']
                yaw = math.atan(slope)
                offset = (straight['near_error'] - 30*slope) * math.cos(yaw)
                reference = _corner_template(offset, 50, yaw, 0)
                if reference is not None:
                    preview_due = self.preview_at is None or now-self.preview_at >= 70
                    if preview_due:
                        self.preview_at = now
                    if not preview_due or not turn_ahead(pixels, threshold, reference):
                        return self._use_straight(straight, reference, now)
        black, occupied, labels = corner_grid(pixels, threshold)
        grid_done = clock() if clock else 0
        anchors = _pair_anchors(black)
        anchors_done = clock() if clock else 0
        tracking = self.previous is not None
        quick, front = None, None
        tried_angle = None
        active_angle = self.previous[4][3] if tracking else 0
        straight_entry = self.joint and tracking and active_angle == 0
        if reference is not None:
            tried_angle = OBTUSE_TURN if self.first_exit is not None else math.pi/2
            match = fitted_outer_l(black, occupied, _corner_template, tried_angle)
            if (match is not None and _same_rail(reference, 0, match) and
                    self.curve(match[4])['entry_distance'] <= 38):
                quick = match
            else:
                return self._use_straight(straight, reference, now)
        if quick is None and self.joint and self.first_exit is not None and not self.second_corner and tried_angle is None:
            # 出直角弯后，只有接在当前出弯车道上的两条实测外臂才能切换弯型。
            match = fitted_outer_l(black, occupied, _corner_template, OBTUSE_TURN)
            if (match is not None and _same_rail(self.first_exit, self.first_exit[4][3], match)
                    and (not anchors or _current_anchor_distance(match, anchors) <= 10)):
                quick = match
        if quick is None and self.predictive and tracking and not anchors and active_angle > 0:
            # 已跟踪的折角先用当前外边直接拟合，节省整组邻居/精化生成。
            # 左臂渐出画后，只关联上帧已确认的前线方向和距离。
            match = fitted_outer_l(black, occupied, _corner_template, active_angle)
            if match is not None and self.distance(match, self.previous) <= 24:
                quick = match
            elif _still_has_l(self.previous, black, occupied):
                quick = self.previous
            elif self.front_at is not None and now-self.front_at < PREDICTION_GAP_MS:
                match = fitted_front_edge(black, self.front_model, _corner_template)
                if match is not None:
                    front_route = _along_exit_edge(match[0], self.outset) or self.curve(match[0][4])['route']
                    if clear_predicted_corridor(pixels, black, threshold, front_route):
                        quick, front = match[0], (match[1], match[2])

        def evaluate(t):
            angle = t[4][3]
            if self.joint and angle > 0:
                if angle > 1 and (self.second_corner or (self.first_exit is not None and active_angle <= 1)):
                    return None
                if angle == OBTUSE_TURN and not self.second_corner and (
                        self.first_exit is None or not _same_rail(self.first_exit, self.first_exit[4][3], t)):
                    return None
            sides, centers = t[0], t[1]
            counts = [sum(occupied[i] for i in side) for side in sides]
            ratios = [counts[j]/max(1, len(sides[j])) for j in (0, 1)]
            if any(black[i] for i in centers):
                return None
            error = _current_anchor_distance(t, anchors) if anchors else 0
            if anchors and error > 10:
                return None
            distance = self.distance(t, self.previous) if self.previous else 0
            same_entry = straight_entry and angle > 0 and _same_rail(self.previous, 0, t)
            if distance > 18 and not same_entry and not (
                    self.joint and angle == OBTUSE_TURN and not self.second_corner):
                return None
            dual = len(centers) >= 3 and all(counts[j] >= 4 and ratios[j] >= 0.55 for j in (0, 1))
            if dual:
                ids = [{labels[i] for i in side if occupied[i]} for side in sides]
                dual = bool(ids[0]-ids[1] and ids[1]-ids[0])
            # 直道必须有逐行双边走廊；转弯允许用两条二维边界证明当前支持。
            dual = dual and (bool(anchors) or angle > 0)
            if self.joint and dual and angle > 0 and (not self.first_corner or (angle == OBTUSE_TURN and not self.second_corner)):
                # 两条平行直边也可能匹配角点模板。从直道切入任何新弯时必须实测同一侧两臂。
                dual = any(all(len(arm) >= 3 and sum(occupied[i] for i in arm) >= max(3, .65 * len(arm))
                               for arm in side) for side in (t[6][:2], t[6][2:]))
            # 当前左外边的入弯臂和出弯臂共同证明折角，不要求右侧边界出现，
            # 也不要求此前先得到双侧许可。只有一根直带不满足此判据。
            corner = False
            associated = False
            min_yaw = -angle - math.radians(5) if angle == OBTUSE_TURN else -math.radians(85)
            if angle > 0 and min_yaw <= t[4][2] <= math.radians(25):
                arms = t[6][:2]  # 只用左外边：左纵边与前方横边，不误用内侧L或文字。
                corner = counts[0] >= 12 and ratios[0] >= 0.75 and all(
                    len(arm)>=3 and sum(occupied[i] for i in arm)>=3
                    and sum(occupied[i] for i in arm)/len(arm)>=0.65 for arm in arms)
                # 中线可能在相机近端盲区，但L的两条边朝道路内侧必须有当前白区。
                # 这仍是当前形状证据，不能用旧图或一根黑直线填补全部视野。
                corner = corner and len(t[8])>=4 and sum(black[i] for i in t[8])<=len(t[8])//5
                # 转弯后仅剩当前出口边时，用上一已确认L的角色作短期关联。
                # 当前仍需12个支持格及白色路径，最多700ms，空白从不续行。
                associated = (not corner and self.corner_at is not None and now-self.corner_at < 700
                    and self.previous is not None and distance<12 and counts[0]>=12 and ratios[0]>=0.75)
            # 没有可见中线时，未通过当前L／当前出口支持的模型仅作精化种子，
            # 不能成为有效路径；否则近端盲区会在粗搜阶段把正确角点邻域一起删掉。
            # 样本仅一格的画外短边不能凭100%命中率压过真正有多点支持的模型。
            score = sum(min(ratios[j], counts[j]/4) for j in (0, 1))
            score += min(sum(counts), 35)*0.018-error*0.10-distance*0.025
            # 出口直线与画外角点模型可能同样解释当前两条直边；优先简单直线，
            # 防止把不可见角点当作仍须大差速的转弯证据。
            if angle > 0: score -= 0.12
            if dual: score += 0.5
            elif corner: score += 0.3
            return score, dual, (2 if corner else (1 if associated else 0)), counts

        templates = self.templates
        if self.joint and self.first_exit is not None:
            if self.second_corner:
                templates = self.straight_templates + self.obtuse_templates
            else:
                templates = self.templates + self.obtuse_templates
        if quick is not None:
            pool = []
        elif tracking:
            c, d, yaw, angle = self.previous[5]
            if self.neighbor_key != self.previous[5]:
                self.neighbor_key = self.previous[5]
                self.neighbors = []
                for dc, dd, dy in ((-3,0,0),(3,0,0),(0,-4,0),(0,4,0),(0,0,-5),(0,0,5)):
                    t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                    if t is not None: self.neighbors.append(t)
            pool = [self.previous]
            pool.extend(self.neighbors)
            # 正常帧只验证上次模型及6个邻居，并滚动查看12个当前粗候选。
            # 仅复用预计算几何，不保留旧像素分数；新的弯道仍能随当前图像进入搜索。
            # 已有模型时不再每帧遍历全库并重建27个细化模板，减少源年龄空档。
            for _ in range(min(12, len(templates))):
                pool.append(templates[self.search_cursor % len(templates)])
                self.search_cursor = (self.search_cursor+1) % len(templates)
        else:
            # 启动／失线重获保留原全库搜索；未经当前支持和稳定门不授予运动许可。
            pool = templates
        seeds = []
        best = quick
        best_score = 2.0 if quick is not None else -1e9
        support = [sum(occupied[i] for i in side) for side in quick[0]] if quick is not None else [0, 0]
        best_dual = False
        best_corner = 2 if quick is not None and front is None else 0
        for t in pool:
            candidate = evaluate(t)
            if candidate is None: continue
            score, dual, single, counts = candidate
            seeds.append((score, t))
            if (dual or single) and score > best_score:
                best, best_score, support = t, score, counts
                best_dual = dual
                best_corner = single
        recovery = 0
        if tracking and best is None:
            # 真实1315→1316帧需要c/d同时变化；六个轴向邻居都失配时，先查8个
            # 耦合邻居再全库重获。仅失败帧构建它们，避免每个正常帧增加投影耗时，
            # 导致处理超过100ms反而撤销许可。每个候选仍走完全相同的当前证据门。
            c,d,yaw,angle=self.previous[5]
            if self.recovery_key != self.previous[5]:
                self.recovery_key=self.previous[5]
                self.recoveries=[]
                offsets=[(dc,dd,0) for dc in (-3,3) for dd in (-4,4)]
                offsets += [(0,dd,dy) for dd in (-4,4) for dy in (-5,5)]
                for dc,dd,dy in offsets:
                    t=_corner_template(c+dc,d+dd,yaw+math.radians(dy),angle)
                    if t is not None:self.recoveries.append(t)
            for t in self.recoveries:
                recovery += 1
                candidate=evaluate(t)
                if candidate is None:continue
                score,dual,single,counts=candidate
                seeds.append((score,t))
                if (dual or single) and score>best_score:
                    best,best_score,support=t,score,counts
                    best_dual=dual;best_corner=single
        forecast = 3 if front is not None else 0
        fitted = quick is not None
        anchor_fresh = self.forecast_anchor_at is not None and now-self.forecast_anchor_at < PREDICTION_ANCHOR_MS
        rail_fresh = self.rail_at is not None and now-self.rail_at < PREDICTION_GAP_MS
        if self.predictive and not best_dual and not fitted:
            # 右边出画时，直接用当前左纵／前横交点补充离散库。当前两臂拟合
            # 成功便跳过整库重扫与27点精化，给测到过峰值的K230留出时间。
            match = fitted_outer_l(black, occupied, _corner_template,
                                   OBTUSE_TURN if self.first_exit is not None else math.pi / 2)
            if (match is not None and (not anchors or _current_anchor_distance(match, anchors) <= 10)
                    and (not tracking or self.distance(match, self.previous) <= 24 or
                         (straight_entry and _same_rail(self.previous, 0, match)))
                    and (not self.joint or self.first_exit is None or self.second_corner or
                         _same_rail(self.first_exit, self.first_exit[4][3], match))):
                best, best_score = match, 2.0
                support = [sum(occupied[i] for i in side) for side in best[0]]
                best_corner = 2
                fitted = True
            elif self.joint and tracking and best_corner != 2 and (anchor_fresh or rail_fresh):
                # 只有当前至少四行测到同一侧，且角度和截距跟上次一致，才逐帧续接直道单边。
                reference = _straight_reference(self.previous, self.racing)
                rail = fitted_straight_rail(black, reference, _corner_template) if reference is not None else None
                if rail is not None:
                    yaw = rail[4][2]
                    nx, nz = math.cos(yaw), -math.sin(yaw)
                    line = [(x - self.outset*nx, z - self.outset*nz) for x, z in rail[2]]
                    if clear_predicted_corridor(pixels, black, threshold, line):
                        best, forecast = rail, 4
                        support = [sum(occupied[i] for i in side) for side in rail[0]]
            if not fitted and not forecast and anchor_fresh:
                # 降级时依次尝试当前单边和短时白走廊。单边重新计算模型；
                # 白走廊只沿最近路线短时前进，不从空白画面生成新转弯。
                if best_corner == 1:
                    forecast = 1
                elif best is None:
                    left_fit = fitted_left_forecast(black, self.previous, _corner_template)
                    if (left_fit is not None and self.distance(left_fit, self.previous) < 12
                            and len(left_fit[1]) >= 4 and not any(black[i] for i in left_fit[1])):
                        best, forecast = left_fit, 1
                        support = [sum(occupied[i] for i in side) for side in best[0]]
                    else:
                        for _, t in sorted(seeds, key=lambda item: -item[0])[:8]:
                            if len(t[1]) < 4 or self.distance(t, self.previous) >= 12:
                                continue
                            counts = [sum(occupied[i] for i in side) for side in t[0]]
                            if any(count >= 9 and count >= 0.62 * len(side) and sum(black[i] for i in side) >= 3
                                   for count, side in zip(counts, t[0])):
                                best, support, forecast = t, counts, 1
                                break
            if (best is None and (anchor_fresh or rail_fresh) and self.visible_edge_at is not None
                    and now-self.visible_edge_at < PREDICTION_GAP_MS
                    and clear_predicted_corridor(pixels, black, threshold, self.forecast_route)):
                best, forecast = self.previous, 2
        fallback = 0
        if tracking and best is None:
            # 局部支持不足时同帧回到完整当前搜索，不能因为滚动库本帧没扫到
            # 邻近新几何而人为制造失线。所有旧关联／单侧／白路面门保持。
            for t in templates:
                # K230运行时搜索达到本帧预算就结束，给封包和串口留余量。
                if self.predictive and clock and clock()-begun >= 78:
                    break
                fallback += 1
                candidate = evaluate(t)
                if candidate is None: continue
                score, dual, single, counts = candidate
                seeds.append((score, t))
                if (dual or single) and score > best_score:
                    best, best_score, support = t, score, counts
                    best_dual = dual
                    best_corner = single
        seeds.sort(key=lambda item: -item[0])
        refined = 0
        # 几何精化保持原27点；只缓存当前seed的预计算模板，分数仍逐帧重算。
        # seed不变时不再每帧重新计算三角函数／投影／折角臂；缓存大小固定。
        for _, seed in (() if fitted or forecast else seeds[:1]):
            c, d, yaw, angle = seed[5]
            if self.refine_key != seed[5]:
                self.refine_key = seed[5]
                self.refinements = []
                offsets = [(dc,dd,dy) for dc in (-6,0,6)
                           for dd in ((0,) if angle == 0 else (-10,0,10)) for dy in (-10,0,10)]
                for dc,dd,dy in offsets:
                    if self.predictive and tracking and clock and clock()-begun >= 78:
                        self.refine_key = None  # 尚未构完，下一帧可补足。
                        break
                    t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                    if t is not None: self.refinements.append(t)
            for t in self.refinements:
                if self.predictive and tracking and clock and clock()-begun >= 84:
                    break
                refined += 1
                candidate = evaluate(t)
                if candidate is None: continue
                score, dual, single, counts = candidate
                if (dual or single) and score > best_score:
                    best, best_score, support = t, score, counts
                    best_dual = dual
                    best_corner = single
        out.update(support=support, searched_candidates=len(pool)+recovery+fallback+refined, vision_mode='corner_search',
                   recovery_candidates=recovery,
                   anchors=len(anchors), search_mode='fallback' if fallback else ('tracking' if tracking else 'acquire'))
        if clock:
            out['profile_ms'] = dict(grid=grid_done-begun, anchors=anchors_done-grid_done,
                                     search=clock()-anchors_done)
        if best is None:
            if self.joint:
                # 模型落空只表示这一帧没有新路线。明确看到旧路线受阻才立即撤许可。
                if self.forecast_route is None or not _corridor_blocked(black, self.forecast_route):
                    out['reason'] = 'observation_missed'
                    return out
                out['reason'] = 'corridor_blocked'
            self.reset()
            self.last_at = now
            return out
        if self.previous is None:
            self.stable = 1; self.stable_at = now
        else:
            self.stable += 1
        self.previous = best
        cx, cz, yaw, angle = best[4]
        if best_corner == 2:
            self.corner_at = now
        exit_aligned = yaw + angle <= math.radians(15)
        if angle == 0 or (angle > 0 and exit_aligned and cz < 10):
            risk = 0
            stage = 'straight' if angle == 0 else 'exit'
        else:
            # 远处先降速；当角点接近或车头已转入弯内时持续低速。
            # 这些量来自当前模板，不是从人工KEY开始累计的转弯时刻。
            risk = max(0.0, min(1.0, (85-cz)/45))
            if yaw < -math.radians(15): risk = 1.0
            stage = 'approach' if cz > 40 and yaw > -math.radians(15) else 'turn'
        valid = self.stable >= 3 and now-self.stable_at >= 80
        if not best_dual and not forecast: risk = 1.0
        # 直道沿用32点误差；有90度几何时下方改用外入切弯圆弧和24点纯追踪。
        target = best[2][6] if risk > 0 else best[2][3]
        steering = max(-1000, min(1000, round(math.atan2(target[0], max(5, target[1]))/math.radians(55)*1000)))
        route = best[2]
        if angle > 0 and (self.joint or not (exit_aligned and cz < 10)):
            if self.racing_key != best[4]:
                self.racing_key = best[4]; self.racing = self.curve(best[4])
            if self.racing is not None:
                route = self.racing['route']; steering = self.racing['steering']
                out['racing_radius'] = self.racing['radius']; out['racing_outset'] = self.racing['outset']
                out['racing_phase'] = self.racing['phase']
                out['arc_entry_distance'] = self.racing['entry_distance']
                out['route_projection_s'] = self.racing['projection_s']
                stage = 'approach' if self.racing['phase']=='entry' else ('turn' if self.racing['phase']=='arc' else 'exit')
                if self.joint and best_dual:
                    # 双边时提前适量减速，钝角用较大半径，回正后释放弯速限制。
                    # 处于弯模型时保留0.2，确保驶出弧后若只剩当前出口边，STM32仍有最近弯道锚点。
                    maximum = 1.0 if angle > 1 else 0.68
                    risk = max(0.2, maximum * (1 - self.racing['entry_distance'] / 38)) if stage != 'exit' else 0.2
        elif self.joint and angle == 0:
            # 直道、首弯出口、第二弯入口都以同一条外偏线为目标。
            nx, nz = math.cos(yaw), -math.sin(yaw)
            route = [(x - self.outset*nx, z - self.outset*nz) for x, z in route]
            x, z = route[3]
            steering = round(max(-1, min(1, math.atan2(x, max(5, z))/math.radians(55)))*1000)
        source = 'current_pair' if best_dual else ('current_corner_predicted' if best_corner == 2 else 'current_corner_associated')
        confidence = 75 if best_dual else (60 if best_corner == 2 else 45)
        if self.predictive and not best_dual and best_corner != 2 and not forecast:
            # 全库重获/精化也可能找到旧式出口单边。和直接找到的单边使用同一时限。
            if self.forecast_anchor_at is None or now-self.forecast_anchor_at >= PREDICTION_ANCHOR_MS:
                forecast = 0
                valid = False
            else:
                forecast = 1
        if forecast:
            # 前方白区有支持才下发预测。暂时无边线只延续已有路线，不更新边线时钟。
            if forecast == 3:
                source, confidence = 'current_front_forecast', 58
                out.update(front_support=front[0], front_distance=front[1])
                exit_route = _along_exit_edge(best, self.outset)
                if exit_route is not None:
                    # 原横线已转成沿行驶方向的左边。用它的法向偏移和新朝向回正。
                    route = exit_route
                    x, z = route[3]
                    steering = max(-1000, min(1000, round(math.atan2(x, max(5, z))/math.radians(55)*1000)))
                    stage, risk = 'exit', 0.0
            elif forecast == 4:
                source, confidence = 'current_straight_rail', 56
                slope = math.tan(yaw)
                near = (best[5][0] - self.outset) / math.cos(yaw) + 30*slope
                steering = round(StraightRoute.command(near, slope)*1000)
            elif forecast == 1:
                source, confidence = 'current_single_forecast', 55
            else:
                source, confidence = 'short_corridor_forecast', 45
                route = self.forecast_route
                if self.joint:
                    steering, risk = self.forecast_command
            valid = valid and clear_predicted_corridor(pixels, black, threshold, route)
        elif not best_dual and not self.joint:
            # v5单侧L／弱关联只允许右转或直行，不扩大协议到未经确认的左转。
            # 推荐点仍在入口直道时不额外给10%右转；真正到达圆弧后，右转量
            # 由连续路线自然增大。双侧路径保留有符号修正，允许及时回正。
            steering = max(0,steering)
        if self.joint and valid:
            # 两边或外侧两臂已确认时，额外核对看得见的实际赛车线；未使用模板假定的黑格。
            if not forecast:
                valid = clear_predicted_corridor(pixels, black, threshold, route, minimum=0)
            if valid:
                self._advance_joint(best, best_dual, best_corner, forecast, now)
                if self.second_exit_at is not None and now - self.second_exit_at >= 450:
                    out['joint_complete'] = True
                out['road_section'] = ('obtuse_exit' if self.second_exit_at is not None else 'obtuse'
                                       if self.second_corner else 'connector' if self.first_exit is not None
                                       else 'right_angle' if angle else 'start_straight')
        if self.predictive and valid:
            if self.joint and forecast == 4:
                self.rail_at = now
            elif self.joint and not forecast and risk >= 0.2:
                self.rail_at = None
            if not forecast or forecast == 3:
                self.forecast_anchor_at = now
                if angle > 0 and (best_corner == 2 or forecast == 3 or round(risk*1000) >= 200):
                    self.front_model, self.front_at = best, now
                else:
                    self.front_model = self.front_at = None
            if forecast != 2:
                self.visible_edge_at = now
                self.forecast_route = route
                self.forecast_command = steering, risk
        # R7实跑出现100→371及负修正→508的切换，来自距离下限覆盖路线。
        # R8取消该下限；留0字段便于与旧逐帧证据比较，不以历史L强行续转。
        out['turn_floor'] = 0
        reason = 'ready' if valid else 'stabilizing'
        if self.joint and not valid:
            # 新拟合可信度不足或白区证据短缺时，既不发新转向也不刷新上一帧的时钟。
            if self.forecast_route is not None and _corridor_blocked(black, self.forecast_route):
                reason = 'corridor_blocked'
            else:
                reason = 'observation_missed'
        out.update(valid=valid, source=source, steering=steering,
                   bend=int(round(risk*1000)), confidence=confidence, stage=stage,
                   corner_observed=best_corner==2, corner_age_ms=0 if self.corner_at is None else now-self.corner_at,
                   measured_edges=('none' if forecast == 2 else 'front' if forecast == 3 else 'single' if forecast == 1 else
                                   'straight_rail' if forecast == 4 else 'left_and_front' if best_corner == 2 else
                                   'pair' if best_dual else 'associated_left'),
                   path_kind='racing_arc_prediction' if angle>0 else 'straight_observation',
                   path_visibility='projected' if best[1] else 'predicted_near_blind',
                   parameters=list(best[4]), route=route, score=best_score,
                   reason=reason)
        return out

    def _advance_joint(self, best, dual, corner, forecast, now):
        """依据现在看到的弧尾或出弯双边推进弯序，毫秒仅用于确认钝角出口。"""
        _, _, yaw, angle = best[4]
        observed = dual or corner == 2 or forecast == 3
        near_exit = (angle > 0 and abs(yaw + angle) <= math.radians(16) and
                     self.racing is not None and self.racing['exit_s'] >= -5)
        last_bend = self.front_model
        connected_exit = False
        if angle == 0 and dual and last_bend is not None:
            _, _, previous_yaw, previous_angle = last_bend[4]
            # 车头转过后原角点可能直接出画，用当前两条出口边确认上一已跟踪弯道。
            if self.racing_key == last_bend[4] and abs(previous_yaw + previous_angle) <= math.radians(20):
                connected_exit = (self.racing['exit_s'] >= -10 and _same_rail(last_bend, previous_angle, best))
        if angle > 1 and not self.second_corner and near_exit and observed:
            self.first_exit = best
        elif not self.second_corner and connected_exit and last_bend[4][3] > 1:
            self.first_exit = best
        elif not self.second_corner and angle == 0 and dual and self.first_exit is not None:
            if _same_rail(self.first_exit, self.first_exit[4][3], best):
                self.first_exit = best
        if angle == OBTUSE_TURN and (dual or corner == 2):
            self.second_corner = True
        if angle > 1 and (dual or corner == 2):
            self.first_corner = True
        if not self.second_corner:
            return
        if angle == OBTUSE_TURN and near_exit and observed:
            self.second_exit = best
        elif connected_exit and last_bend[4][3] == OBTUSE_TURN:
            self.second_exit = best
        # 有出弯双边，或实测外边且车头已越过切点，才开始连续观察出口；
        # 单条无新证据的历史路线不能让本段正常结束。
        exit_now = (self.second_exit is not None and
                    ((angle == 0 and dual and _same_rail(self.second_exit, self.second_exit[4][3], best)) or
                     (angle == OBTUSE_TURN and near_exit and observed and self.racing['exit_s'] >= 12)))
        if exit_now:
            if angle == 0:
                self.second_exit = best
            if self.second_exit_at is None:
                self.second_exit_at = now
        else:
            self.second_exit_at = None

# BEGIN right_angle_protocol.py
"""首弯v5：双侧、当前L形预测、短时出口关联分别编码，不发START。"""
try:
    import ustruct as struct
except ImportError:
    import struct


class RightAngleSender(LapSender):
    wire_version = 5
    flags_by_source = {'current_pair': 1, 'current_corner_predicted': 9, 'current_corner_associated': 5}

    def _send(self, data):
        converted = bytearray(data)
        converted[2] = self.wire_version
        checksum = crc16(converted[:18])
        converted[18] = checksum & 255
        converted[19] = checksum >> 8
        return super()._send(bytes(converted))

    def path(self, result, processing_ms, age_ms):
        """v5 bit3为当前左纵／前横L，bit2为有当前支持的短期出口关联。
        不接收纯历史或普通一根单直边；当前L不依赖先前双侧，可人工启动右转。
        """
        if not isinstance(processing_ms,int) or not isinstance(age_ms,int) or min(processing_ms,age_ms)<0:
            raise ValueError('explicit nonnegative timing required')
        kind=result.get('source'); flags=self.flags_by_source.get(kind,0)
        valid=bool(self.allow_drive and result.get('valid') and flags and processing_ms<=100 and age_ms<150)
        steering=int(result.get('steering',0));bend=int(result.get('bend',0));quality=int(result.get('confidence',0))
        if kind=='current_corner_predicted':
            # 联合弯外边仍确认右转，但允许赛车线在进／出弯短时向左回正。
            valid=valid and result.get('corner_observed') is True and bend==1000 and (self.wire_version >= 10 or steering>=0) and quality>=60
        elif kind=='current_corner_associated':
            evidence_age=result.get('corner_age_ms',700)
            valid=valid and isinstance(evidence_age,int) and 0<=evidence_age<700 and bend==1000 and steering>=0 and quality>=45
        elif kind == 'current_front_forecast':
            valid = valid and quality == 58 and result.get('front_support', 0) >= 5
        elif kind == 'current_straight_rail':
            valid = valid and quality == 56 and bend == 0
        elif kind == 'straight_pair':
            valid = valid and quality == 80 and bend == 0
        elif kind in ('current_single_forecast', 'short_corridor_forecast'):
            valid = valid and (50 <= quality < 58 if kind == 'current_single_forecast' else 40 <= quality < 50)
        if not (-1000<=steering<=1000 and 0<=bend<=1000 and 0<=quality<=100):raise ValueError('v5 route fields')
        header=bytes((0xa5,0x5a,self.wire_version,1,12,self.seq));self.seq=(self.seq+1)&255
        data=header+struct.pack('<BBhHHHBB',flags if valid else 0,quality if valid else 0,
            steering if valid else 0,min(age_ms,1000),bend if valid else 0,min(processing_ms,1000),0,0)
        return self._send(data+struct.pack('<H',crc16(data)))

# BEGIN voice_keywords.py
"""K230 ??????????????????????????"""
import time

RATE = 16000
CHUNK = 4800  # 已有KWS模型每次输入300ms单声道PCM。
CHUNK_MS = 300
WAVDIR = '/sdcard/examples/utils/'
REPLIES = ('', 'wozai.wav', 'go_new.wav', 'stop_new.wav', 'wow_new.wav')
READY_REPLY = 1  # 复用已有的“我在”语音，不额外分发WAV。
GO = 2
STOP = 3

class VoiceKeywords:
    """沿用现有KPU模型、MIC增益、分类及右声道功放。模型和Audio均由本脚本独占。"""

    def __init__(self, mapping, go_pcm=None):
        from machine import Pin, FPIOA
        from media.pyaudio import PyAudio, paInt16, LEFT_RIGHT
        import media.wave as wave
        import nncase_runtime as nn
        import ulab.numpy as np
        import aidemo
        import struct

        self.wave, self.nn, self.np = wave, nn, np
        self.aidemo, self.struct = aidemo, struct
        self.input = self.output = self.fp = self.kpu = self.amp = None
        self.last = 0
        self.go_ready = False  # 上电或播报后先听到背景，防重复触发或把扬声器当发令。
        self.ignore_until = None
        # 联合弯的“收到”在上电时转换为整块右声道PCM，识别后不读卡、不转码。
        self.go_audio = tuple(self.stereo(go_pcm[i:i + CHUNK * 2])
                              for i in range(0, len(go_pcm), CHUNK * 2)) if go_pcm else ()
        self.audio = PyAudio()
        try:
            for name in REPLIES[1:]:
                wav = self.open_reply(name)
                wav.close()
            nn.shrink_memory_pool()
            self.fp = aidemo.kws_fp_create()
            self.kpu = nn.kpu()
            self.kpu.load_kmodel('/sdcard/examples/kmodel/multi_kws.kmodel')
            self.cache = np.zeros((1, 256, 105), dtype=np.float)
            mapping.set_function(10, FPIOA.GPIO10)
            self.amp = Pin(10, Pin.OUT, pull=Pin.PULL_NONE, drive=7)
            self.amp.value(1)
            self.input = self.audio.open(format=paInt16, channels=1, rate=RATE,
                                         input=True, frames_per_buffer=CHUNK)
            self.output = self.audio.open(format=paInt16, channels=2, rate=RATE,
                                          output=True, frames_per_buffer=CHUNK)
            self.input.volume(40)
            self.output.volume(100, LEFT_RIGHT)
        except BaseException:
            self.close()
            raise

    def open_reply(self, name):
        wav = self.wave.open(WAVDIR + name, 'rb')
        if (wav.get_framerate(), wav.get_sampwidth(), wav.get_channels()) != (RATE, 2, 1):
            wav.close()
            raise ValueError('Invalid reply WAV: ' + name)
        return wav

    def poll(self):
        """最多读取一块，CanMV v1.8短等待10ms。返回新命中标签，0代表没有命令。"""
        pcm = self.input.read(block=False)
        if self.ignore_until is not None:
            if time.ticks_diff(time.ticks_ms(), self.ignore_until) >= 0:
                self.ignore_until = None
            return 0  # 继续取出并丢弃播报及尾音采样，保持麦克风队列新鲜。
        if pcm is None:
            return 0
        if len(pcm) != CHUNK * 2:
            raise ValueError('Unexpected KWS PCM frame length')
        samples = [self.struct.unpack_from('<h', pcm, offset)[0] for offset in range(0, len(pcm), 2)]
        mean = sum(samples) / CHUNK
        normalized = [sample - mean for sample in samples]
        features = self.aidemo.kws_preprocess(self.fp, normalized)[0]
        self.kpu.set_input_tensor(0, self.nn.from_numpy(self.np.array(features).reshape((1, 30, 40))))
        self.kpu.set_input_tensor(1, self.nn.from_numpy(self.cache))
        self.kpu.run()
        logits = self.kpu.get_output_tensor(0).to_numpy()
        self.cache = self.kpu.get_output_tensor(1).to_numpy()
        scores = self.np.max(logits, axis=1)[0]
        label = int(self.np.argmax(scores)) if float(self.np.max(scores)) > 0.5 else 0
        previous = self.last
        self.last = label
        if label == 0:
            self.go_ready = True
        if label == GO:
            ready = self.go_ready
            self.go_ready = False
            return GO if ready else 0
        return label if label != previous else 0

    def play(self, label):
        """仅在没有活跃运行窗口或刚发STOP后调用，因为WAV及扬声器可阻塞。"""
        wav = self.open_reply(REPLIES[label])
        started = time.ticks_ms()
        frames = 0
        try:
            pcm = wav.read_frames(CHUNK)
            while pcm:
                # 输出设备要求整块大小，末块补零；沿用已有单声道转右路的接法。
                if self.output.write(self.stereo(pcm)) != 0:
                    raise OSError('Speaker write failed')
                frames += 1
                self.input.read(block=False)
                pcm = wav.read_frames(CHUNK)
        finally:
            wav.close()
        self.after_reply(started, frames, CHUNK_MS * 2)

    @staticmethod
    def stereo(pcm):
        """把16位单声道样本送到车载右路功放，末块补零到300ms。"""
        stereo = bytearray(CHUNK * 4)
        for sample_at in range(0, len(pcm), 2):
            stereo[sample_at * 2 + 2:sample_at * 2 + 4] = pcm[sample_at:sample_at + 2]
        return stereo

    def acknowledge_go(self):
        """识别Go后立即送入已缓存的“收到”，此时尚未发送车辆START。"""
        started = time.ticks_ms()
        for block in self.go_audio:
            if self.output.write(block) != 0:
                raise OSError('Speaker write failed')
            self.input.read(block=False)
        self.after_reply(started, len(self.go_audio), 100)

    def after_reply(self, started, frames, tail_ms):
        """丢弃扬声器回采的尾音，再恢复本地Stop识别。参数均为块数或毫秒。"""
        self.cache = self.np.zeros((1, 256, 105), dtype=self.np.float)
        self.last = 0
        self.go_ready = False
        remaining = max(0, frames * CHUNK_MS - time.ticks_diff(time.ticks_ms(), started))
        self.ignore_until = time.ticks_add(time.ticks_ms(), remaining + tail_ms)

    def close(self):
        """逐项释放资源，设备清理失败时仍继续关功放及销毁特征提取器。"""
        actions = []
        for stream in (self.input, self.output):
            if stream is not None:
                actions.extend((stream.stop_stream, stream.close))
        actions.append(self.audio.terminate)
        if self.amp is not None:
            actions.append(lambda: self.amp.value(0))
        if self.fp is not None:
            actions.append(lambda: self.aidemo.kws_fp_destroy(self.fp))
        for action in actions:
            cleanup(action)
        self.kpu = self.cache = None


def cleanup(action):
    try:
        action()
    except BaseException as exc:
        print('[VOICE CLEANUP]', repr(exc))

# BEGIN right_angle_voice_canmv.py
"""K230 语音首弯、分置信度续行和只读手机图传入口。"""
import json
import os
import time

# STM32最多运行12000ms，从发送Go起再给150ms留出串口及本板调度余量。
RUN_WINDOW_MS = 12150
JOINT_RUN_WINDOW_MS = 40150  # 正常看见第二弯出口即结束；含STM32 40秒上限及150ms调度余量。
FRAME_BYTES = 320 * 240
RECORD_LIMIT = 768
PHOTO_LIMIT = 8


class RightAngleVoiceSender(RightAngleSender):
    wire_version = 9
    flags_by_source = {'current_pair': 1, 'current_corner_predicted': 9,
                       'current_single_forecast': 5, 'short_corridor_forecast': 5,
                       'current_front_forecast': 5}

    def start(self, packet):
        """刚发出的当前双侧或当前L形可起步，当前出口弱关联仅许可续行。"""
        if packet[6] not in (1, 9) or packet[7] < 40:
            raise ValueError('Go requires current pair or L corner')
        return send_voice_start(self, packet)


class JointAngleVoiceSender(RightAngleVoiceSender):
    """联合弯配对沿用20字节帧，80／56标记旧直道双边／当前直道单边。"""
    wire_version = 12
    flags_by_source = dict(RightAngleVoiceSender.flags_by_source, current_straight_rail=5, straight_pair=1)


class RunEvidence:
    """一次发令窗口的固定容量日志。只在STOP发出或窗口结束后写入/data。"""

    def __init__(self, wire_version=9):
        self.wire_version = wire_version
        self.last_pixels = bytearray(FRAME_BYTES)
        self.reset()

    def reset(self):
        self.records = [None] * RECORD_LIMIT
        self.photos = [None] * PHOTO_LIMIT
        self.issue = ()
        self.count = self.photo_count = 0
        self.last = self.last_photo_at = self.go_at = None

    def record(self, pixels, result, packet, started, sent, acquired, kws_ms, previous_phone_ms):
        """串口发送后记一帧。时间均为K230毫秒，照片保留相机原灰度。

        age_at_next估算上一帧在本次发送时的年龄，包含2ms名义串口时间；
        首次无效或本地年龄跨200ms时单独保留相邻图，供配对STM32停车环。
        """
        sent_packet = packet is not None
        seq, flags, quality = (packet[5], packet[6], packet[7]) if sent_packet else (None, None, None)
        previous = self.last
        age_at_next = None if previous is None else time.ticks_diff(sent, previous[0]) + 2
        stage = result['stage']
        row = (started, seq, flags, stage, result['reason'], result['steering'], result['bend'],
               time.ticks_diff(acquired, started), time.ticks_diff(sent, started),
               None if previous is None else time.ticks_diff(sent, previous[1]), age_at_next, kws_ms,
               quality, result['source'], previous_phone_ms)
        if self.wire_version >= 10:
            row += (result.get('road_section'),)
        if self.wire_version >= 12:
            row += (sent_packet, result.get('vision_mode'), result.get('support'), result.get('searched_candidates'),
                    result.get('arc_entry_distance'), result.get('geometry_failures'))
        self.records[self.count % RECORD_LIMIT] = row
        self.count += 1
        if not self.issue and ((sent_packet and not flags) or (age_at_next is not None and age_at_next >= 200)):
            before = () if previous is None else ((previous[0], previous[2], bytes(self.last_pixels)),)
            self.issue = before + ((started, seq if sent_packet else 256, bytes(pixels)),)
        if not sent_packet:
            return  # 保留最近真实PATH的时间、序号和画面，无包帧不能刷新源年龄。
        if (self.last_photo_at is None or stage != previous[3] or
                time.ticks_diff(started, self.last_photo_at) >= 1000):
            self.photos[self.photo_count % PHOTO_LIMIT] = (started, seq, bytes(pixels))
            self.photo_count += 1
            self.last_photo_at = started
        self.last_pixels[:] = pixels
        self.last = (started, sent, seq, stage)

    def save(self, event, at, error=None):
        """每次发令使用独立文件名。写入错误报告到终端，且不会触发新的运动。"""
        if self.go_at is None:
            return
        folder = '/data/right_angle_logs'
        try:
            os.stat(folder)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
            os.mkdir(folder)
        for index in range(1, 1001):
            prefix = folder + '/voice_%04d' % index
            try:
                os.stat(prefix + '.jsonl')
            except OSError as exc:
                if not exc.args or exc.args[0] != 2:
                    raise
                break
        else:
            raise RuntimeError('right-angle voice log slots exhausted')
        columns = ('start_ms', 'seq', 'flags', 'stage', 'reason', 'steering', 'bend', 'acquire_ms',
                   'to_send_ms', 'send_interval_ms', 'previous_source_age_ms', 'kws_ms',
                   'confidence', 'source', 'previous_phone_ms')
        if self.wire_version >= 10:
            columns += ('road_section',)
        if self.wire_version >= 12:
            columns += ('transmitted', 'vision_mode', 'support', 'searched_candidates', 'arc_entry_distance',
                        'straight_geometry_failures')
        with open(prefix + '.jsonl', 'w') as log:
            log.write(json.dumps(dict(event=event, script_error=error, time_ms=at, go_sent_ms=self.go_at, wire_version=self.wire_version,
                dropped_records=max(0, self.count - RECORD_LIMIT),
                columns=columns)) + '\n')
            for count in range(max(0, self.count - RECORD_LIMIT), self.count):
                log.write(json.dumps(self.records[count % RECORD_LIMIT]) + '\n')
        for group, photos in (('route', self.photos), ('issue', self.issue)):
            for photo in photos:
                if photo is not None:
                    at_ms, seq, raw = photo
                    with open('%s_%s_%d_%03d.pgm' % (prefix, group, at_ms, seq), 'wb') as pgm:
                        pgm.write(b'P5\n320 240\n255\n')
                        pgm.write(raw)
        print('[RIGHT ANGLE VOICE LOG]', prefix, event, self.count)

    def finish(self, event, at, error=None):
        cleanup(lambda: self.save(event, at) if error is None else self.save(event, at, error))
        self.reset()


def drive(sensor, channel, gray, sender, voice, evidence, phone=None, joint=False):
    """一轮先采并发送PATH，再读一次短等待音频。Go发令始终绑定新鲜PATH序号。

    单L及出口弱关联按当前图像续行。联合版模型暂未匹配、且无明确压线证据时等下一帧，
    STM32仍以最后发出的源图年龄监督。明确阻断的无效帧立即发出。
    车上没有执行回执，窗口表示已发Go。窗口内不打印、不播放WAV、不写存储。
    """
    detector = RightAngleRoute(predictive=True, joint=joint)
    origin = time.ticks_ms()
    detector.clock = lambda: time.ticks_diff(time.ticks_ms(), origin)
    voice.play(READY_REPLY)
    pending_go = run_until = None
    phone_ms = 0
    print('[RIGHT ANGLE VOICE] ready v%d' % sender.wire_version)
    while True:
        os.exitpoint()
        started = time.ticks_ms()
        frame = sensor.snapshot(chn=channel)
        acquired = time.ticks_ms()
        if (frame.width(), frame.height(), frame.format()) != (320, 240, gray):
            raise ValueError('Expected a 320x240 grayscale frame')
        pixels = frame.bytearray()
        copied = time.ticks_ms()
        result = detector.update(pixels, time.ticks_diff(started, origin))
        processed = time.ticks_ms()
        processing = time.ticks_diff(processed, copied)
        age = time.ticks_diff(processed, started)
        skip = (joint and run_until is not None and (result['reason'] == 'observation_missed' or
                (result['valid'] and (processing > 100 or age >= 150))))
        # 跳过不确证或过期帧，不更新时间戳。语音Stop和本地记录完成逻辑照常处理。
        packet = None if skip else sender.path(result, processing, age)
        sent = time.ticks_ms()
        if pending_go is not None:
            remaining = (700 if joint else 200) - time.ticks_diff(sent, pending_go)
            if packet[6] in (1, 9) and packet[7] >= 40 and remaining > 0:
                evidence.go_at = sent  # 串口异常时finally仍可保存窗口起点。
                sender.start(packet)
                run_until = time.ticks_add(sent, JOINT_RUN_WINDOW_MS if joint else RUN_WINDOW_MS)
                evidence.record(pixels, result, packet, started, sent, acquired, 0, phone_ms)
                pending_go = None
                continue
            if not joint or remaining <= 0:
                print('[RIGHT ANGLE VOICE] go_blocked', result['reason'])
                pending_go = None
            if not joint:
                continue
        keyword = voice.poll()
        recognized = time.ticks_ms()
        completed = joint and run_until is not None and packet is not None and packet[6] and result.get('joint_complete', False)
        if keyword == STOP or completed:
            pending_go = None
            for _ in range(3):
                sender.stop()
        if run_until is not None:
            if packet is not None or joint:
                evidence.record(pixels, result, packet, started, sent, acquired, time.ticks_diff(recognized, sent), phone_ms)
            if keyword == STOP or completed or time.ticks_diff(recognized, run_until) >= 0:
                event = 'stop_sent' if keyword == STOP else 'joint_complete' if completed else 'go_window_elapsed'
                evidence.finish(event, recognized)
                run_until = None
                if joint:
                    detector.reset()
                if keyword == STOP or not joint:
                    voice.play(STOP if keyword == STOP else GO)
        elif keyword == STOP:
            voice.play(STOP)
        elif keyword == GO and pending_go is None:
            if joint:
                # 先说“收到”，然后重新采一张图再发START。播报期间车辆尚未启动。
                voice.acknowledge_go()
            pending_go = time.ticks_ms() if joint else recognized
        elif keyword in (1, 4):
            voice.play(keyword)
        if phone is not None:
            # 待机没有动力窗口，继续更新手机画面，避免场景复杂时65ms门一直挡住JPEG。
            # Go已识别时先等下一张控制图；运行期间仅在有足够路径时序余量时编码。
            # 原始取证已复制，图传异常只关闭预览，不能中断首弯控制循环。
            phone_at = time.ticks_ms()
            encode_allowed = pending_go is None and (
                run_until is None or time.ticks_diff(phone_at, started) <= 65)
            try:
                phone.step(frame, result, packet, encode_allowed)
            except Exception:
                cleanup(phone.close)
                phone = None
            phone_ms = time.ticks_diff(time.ticks_ms(), phone_at)
        else:
            phone_ms = 0


def main(joint=False, go_pcm=None):
    """初始化既有GC2093、UART2和语音资源。上电等待本地Go，退出先撤驱动。"""
    from machine import FPIOA, UART
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.media import MediaManager
    import image

    sensor = uart = sender = voice = evidence = phone = error = None
    media = False
    try:
        if not joint:
            phone = open_phone_preview()
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS,
                    parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender_type = JointAngleVoiceSender if joint else RightAngleVoiceSender
        sender = sender_type(uart.write, allow_drive=True)
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=320, height=240, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False)
        sensor.set_vflip(False)
        MediaManager.init()
        media = True
        voice = VoiceKeywords(mapping, go_pcm)
        evidence = RunEvidence(sender.wire_version)
        sensor.run()
        drive(sensor, CAM_CHN_ID_0, image.GRAYSCALE, sender, voice, evidence, phone, joint)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        if sender is not None:
            def stop_link():
                sender.stop()
                time.sleep_ms(10)  # 给最后一个20字节帧留出完成串口发送的时间。
            cleanup(stop_link)
        if sensor is not None:
            cleanup(sensor.stop)
        if evidence is not None and evidence.go_at is not None:
            evidence.finish('script_exit', time.ticks_ms(), error)
        if voice is not None:
            cleanup(voice.close)
        if phone is not None:
            cleanup(phone.close)
        if media:
            time.sleep_ms(100)
            cleanup(MediaManager.deinit)
        if uart is not None:
            cleanup(uart.deinit)


if __name__ == '__main__':
    main(joint=True, go_pcm=GO_RECEIVED_PCM)
