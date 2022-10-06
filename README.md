# MSR_MusicGrabber
方舟音樂下載器之類的
包含音樂本體、封面圖以及歌詞（如果有的話）
來源是鷹角官網 - 塞壬唱片
Download music, album cover art and lyrics(.lrc if exists) from Arknights official website

預設將簡體內容轉換為繁體，但不包含歌詞檔
Simplified chinese contents(filename, ID3 Tags... except lyric files)

# 執行環境需求 / Requirements
* Python3
* Python libraries: requests, sanitize_filename, pydub, mutagen, opencc
* ffmpeg
