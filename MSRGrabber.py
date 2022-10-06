import requests
import json
import os
import re
from sanitize_filename import sanitize
from pydub import AudioSegment
from mutagen.flac import Picture, FLAC
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from multiprocessing import Process, Pool
from opencc import OpenCC


TARGET_DIR = "Downloaded"

def createDir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

def getFileExt(filename):
    ext = re.search(r"\.\w*$", filename)
    if(ext):
        return ext.group(0)
    else:
        return ""

def downloadFile(url, pathName):
    raw = requests.get(url)
    open(pathName, "wb").write(raw.content)

def postproc(inPath, tags, coverPath):
    print("音檔後處理"+"："+inPath)
    mime = 'image/jpeg'
    if(coverPath):
        if(getFileExt(coverPath) == ".png"):
            mime = 'image/png'

    if(getFileExt(inPath) == ".wav"):
        outPath = re.sub(r"\.\w*$", ".flac", inPath)
        songFile = AudioSegment.from_wav(inPath)
        songFile.export(outPath, format = "flac")
        os.remove(inPath)
        songFileMutagen = FLAC(outPath)
        if(coverPath):            
            image = Picture()
            image.type = 3
            image.mime = mime
            image.desc = 'front cover'
            with open(coverPath, 'rb') as f:
                image.data = f.read()
            songFileMutagen.add_picture(image)
    if(getFileExt(inPath) == ".mp3"):
        if(coverPath):
            songID3 = ID3(inPath)
            with open(coverPath, 'rb') as albumart:
                songID3['APIC'] = APIC(
                    encoding=3,
                    mime=mime,
                    type=3, desc=u'Cover',
                    data=albumart.read()
                )
            songID3.save()
        songFileMutagen = EasyID3(inPath)
    for key, value in tags.items():
        songFileMutagen[key] = value
    songFileMutagen.save()


if(__name__ == "__main__"):
    downloadCount = 0
    queue = list()
    cc = OpenCC('s2t')
    createDir(TARGET_DIR)
    allSongListObj = json.loads(requests.get("https://monster-siren.hypergryph.com/api/songs").text)
    albumCidSet = set()
    for song in allSongListObj['data']['list']:
        albumCidSet.add(song['albumCid'])
    for albumCid in albumCidSet:
        albumObj = json.loads(cc.convert(requests.get("https://monster-siren.hypergryph.com/api/album/"+albumCid+"/detail").text))
        album = albumObj['data']
        #things in album:cid(album cid), name, intro, belong, coverUrl, coverDeUrl, songs<list>[{cid(song cid), name, artistes<list>},...]
        print("\n\n目前專輯："+album['name'])
        print("歌曲：\n"+"\n".join(album['name'] for album in album['songs']))
        albumPath = os.path.join(TARGET_DIR,album['name'])
        createDir(albumPath)
        coverPath = None
        if(album['coverUrl']):
            coverPath = os.path.join(albumPath, "cover"+getFileExt(album['coverUrl']))
            downloadFile(album['coverUrl'], coverPath)


        for idx, song in enumerate(album['songs']):
            downloadCount += 1
            print("正在下載("+str(downloadCount)+"/"+str(len(allSongListObj['data']['list']))+")："+album['name']+" - "+song['name'])
            songObj = json.loads(cc.convert(requests.get("https://monster-siren.hypergryph.com/api/song/"+song['cid']).text))
            song = songObj['data']
            songName = sanitize(str(idx+1).zfill(2)+" "+song['name'])
            songExt = getFileExt(song['sourceUrl'])
            #things in song:cid(album cid), name, albumCid, sourceUrl, lyricUrl, mvUrl, mvCoverUrl, artists<list>
            if(song['sourceUrl']):
                downloadFile(song['sourceUrl'], os.path.join(albumPath, songName + songExt))
                queue.append((
                    os.path.join(albumPath, songName + songExt),
                    {
                        'title': song['name'],
                        'artist': ", ".join(song['artists']),
                        'albumartist': ", ".join(song['artists']),
                        'album': album['name'],
                        'tracknumber': str(idx+1)
                    },
                    coverPath
                ))
            if(song['lyricUrl']):
                downloadFile(song['lyricUrl'], os.path.join(albumPath, songName + getFileExt(song['lyricUrl'])))

    pool = Pool(4)
    pool.starmap(postproc, queue)
