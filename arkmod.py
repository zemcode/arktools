#!/usr/bin/python3

import os
import struct
import shutil
import logging
import subprocess
import requests
import urllib.parse, zlib, sys

steamcmd = '/home/steam/steamcmd/steamcmd.sh'
install_dir = '/home/steam/ARK'

mod_dir = os.path.join(install_dir, 'steamapps', 'workshop', 'content', '346110')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

def extract_file(dst, src):
  #logger.info('extract_file: {} <- {}'.format(dst, src))
  size = 0
  with open(dst, 'wb') as wf:
    with open(src,'rb') as rf:
      # check
      sig = rf.read(8)
      if sig != b'\xC1\x83\x2A\x9E\x00\x00\x00\x00':
        logger.error('Bad file magic')
        return

      chunk_size_lo, chunc_size_hi, comproto_lo, comproto_hi, uncomtot_lo, uncomtot_hi = struct.unpack('<IIIIII', rf.read(24))

      chunks = []
      comprused = 0

      while comprused < comproto_lo:
        comprsize_lo, comprsize_hi, uncomsize_lo, uncomsize_hi = struct.unpack('<IIII', rf.read(16))
        chunks.append(comprsize_lo)
        comprused += comprsize_lo

      for comprsize in chunks:
        b = zlib.decompress(rf.read(comprsize))
        size += len(b)
        wf.write(b)

       
  return size

def extract_mod(modid):
  for curdir, subdirs, files in os.walk(os.path.join(mod_dir, str(modid), 'WindowsNoEditor')):
    for file in files:
      name, ext = os.path.splitext(file)
      if ext != '.z': continue

      src = os.path.join(curdir, file)
      dst = os.path.join(curdir, name)
      uncompressed = os.path.join(curdir, file + '.uncompressed_size')

      real_size = extract_file(dst, src)

      with open(uncompressed, 'r') as f:
        expect_size = int(f.read())
   
      if real_size != expect_size:
        logger.error('extract_file: uncompressed_size is incorrect')
        return

      os.unlink(src)
      os.unlink(uncompressed)

def read_ue4_string(f):
  l = struct.unpack('i', f.read(4))[0]
  if l <= 0: return ''
  return f.read(l)[:-1].decode()

def write_ue4_string(f, s):
  f.write(struct.pack('i', len(s)+1))
  f.write(bytearray(s, 'utf-8'))
  f.write(b'\x00')

def create_mod_file(modid):
  # parse mod.info
  map_names = []
  with open(os.path.join(mod_dir, str(modid), 'WindowsNoEditor', 'mod.info'),'rb') as f:
    mod_name = read_ue4_string(f)
    map_count = struct.unpack('i', f.read(4))[0]

    for i in range(map_count):
      cur_map = read_ue4_string(f)
      map_names.append(cur_map)

  # parse modmeta.info
  meta = {}
  with open(os.path.join(mod_dir, str(modid), 'WindowsNoEditor', 'modmeta.info'),'rb') as f:
    total_pairs = struct.unpack('i', f.read(4))[0]
    for i in range(total_pairs):
      key = read_ue4_string(f)
      value = read_ue4_string(f)

      if key and value:
        meta[key] = value

  # write
  with open(os.path.join(mod_dir, str(modid), 'WindowsNoEditor', '.mod'),'w+b') as f:
    f.write(struct.pack('Ixxxx', modid))
    write_ue4_string(f, 'ModName')
    write_ue4_string(f, '')

    # write map_names
    f.write(struct.pack('i', len(map_names)))
    for m in map_names:
      write_ue4_string(f, m)

    f.write(struct.pack('I', 4280483635))
    f.write(struct.pack('i', 2))

    if 'ModType' in meta:
      f.write(struct.pack('p', b'1'))
    else:
      f.write(struct.pack('p', b'0'))

    f.write(struct.pack('i', len(meta)))
    for k,v in meta.items():
      write_ue4_string(f, k)
      write_ue4_string(f, v)

def install_mod(modid):
  target = os.path.join(install_dir, 'ShooterGame', 'Content', 'Mods', str(modid))
  source = os.path.join(mod_dir, str(modid), "WindowsNoEditor")

  if os.path.isdir(target):
    shutil.rmtree(target)

  shutil.copytree(source, target)
  shutil.move(target+'/.mod', target+'.mod')


def download_mods(modids):
  if len(modids) == 0: return [],[]

  cmd = []
  cmd.extend([steamcmd])
  cmd.extend(['+force_install_dir', install_dir])
  cmd.extend(['+login', 'anonymous'])
  for modid in modids:
    cmd.extend(['+workshop_download_item', '346110', str(modid)])
  cmd.extend(['+workshop_status', '346110'])
  cmd.extend(['+quit'])

  outs = []
  with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
    for line in proc.stdout:
      out = line.decode('utf-8').strip()
      outs.append(out)
      logger.info('process stdout: {}'.format(out))
    logger.info('process return: {}'.format(proc.returncode))


  success_mods = []
  failed_mods = []
# TODO XXX
  for modid in modids:
    if not os.path.isdir(os.path.join(mod_dir, str(modid))):
      failed_mods.append(modid)
      continue

    success_mods.append(modid)

    updated = parse_mod_updated(modid)
    with open(os.path.join(mod_dir, str(modid), "WindowsNoEditor", 'updated_time'), 'w+') as f:
      f.write(str(updated))

  return success_mods, failed_mods

def parse_mod_updated(modid):
  appworkshop_file = os.path.join(install_dir, 'steamapps', 'workshop', 'appworkshop_346110.acf')
  if os.path.isfile(appworkshop_file):
    with open(appworkshop_file, 'r') as f:
      for line in f:
        cur = line.strip()
        if cur == "{":
          name = prev.strip('"')
        elif '"timeupdated"' in cur:
          updated = cur.split()[1].strip('"')
          if modid != int(name): continue
          return int(updated)
        prev = cur
  return 0

def get_local_mod_updated(modid):
  filepath = os.path.join(install_dir, 'ShooterGame', 'Content', 'Mods', str(modid), 'updated_time')
  if not os.path.isfile(filepath):
    return 0

  with open(filepath,'r') as f:
    updated_time = int(f.read())

  return updated_time


def get_workshop_mod_updated(modid):
  resp = requests.post(url='http://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1',
                       data={'itemcount':'1', 'publishedfileids[0]': modid})

  if not resp.ok:
    err = Exception('HTTP', 'HTTP request failure: {}'.format(resp.reason))
    logger.error(err)
    raise err

  if resp.json()['response']['publishedfiledetails'][0]['result'] != 1:
    err = Exception('Response', 'failed to get published file details')
    logger.error(err)
    raise err

  j = resp.json()
  updated = j['response']['publishedfiledetails'][0]['time_updated']

  return int(updated)

def has_mod_update(modid):
  local = get_local_mod_updated(modid)
  worksh = get_workshop_mod_updated(modid)

  if local == worksh:
    logger.info("latest version: %s local(%s) == ws(%s)", modid, local, worksh)
    return False
  elif local < worksh:
    logger.info("old version: %s local(%s) < ws(%s)", modid, local, worksh)
    return True
  else:
    err = Exception('MODManager', 'workshop updated time is before local updated time: {} local({}) > ws({})'.format(modid, local, worksh))
    logger.error(err)
    raise err


modids = [569786012,1999447172,1609138312,1315534671,2182894352,1551199162,2198615778,849985437] 

def main():
  update_modids = []
  for modid in modids:
    if not has_mod_update(modid):
      continue

    update_modids.append(modid)

  if not update_modids:
    logger.info("all mods are up-to-date")

  success_mods, failed_mods = download_mods(update_modids)
  if failed_mods:
    logger.error('failed to download mods: {}'.format(failed_mods))

  for modid in success_mods:
    extract_mod(modid)
    create_mod_file(modid)
    install_mod(modid)

if __name__ == '__main__':
  main()
