#!/usr/bin/env python3
"""
Скрипт для скачивания видео с YouTube в форматах mp4 и mp3
Поддерживает отдельные видео и плейлисты
Использование:
    python youtube_downloader.py <URL> --format [mp4|mp3|both]
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("❌ Ошибка: библиотека yt-dlp не установлена")
    print("Установите её командой: pip install yt-dlp")
    sys.exit(1)


def check_if_playlist(url):
    """Проверяет, является ли URL плейлистом"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                return True, info.get('title', 'Неизвестный плейлист'), len(list(info['entries']))
            return False, None, 1
        except Exception:
            return False, None, 1


def try_get_cookies():
    """Пытается получить cookies из доступных браузеров"""
    browsers = ['safari', 'chrome', 'chromium', 'firefox', 'edge', 'opera', 'brave']
    
    for browser in browsers:
        try:
            # Пробуем создать временный YoutubeDL объект для проверки cookies
            test_opts = {'cookiesfrombrowser': (browser,), 'quiet': True}
            with yt_dlp.YoutubeDL(test_opts) as ydl:
                print(f"✓ Используем cookies из {browser.title()}")
                return (browser,)
        except Exception:
            continue
    
    print("⚠️  Cookies из браузера недоступны, скачиваем без авторизации")
    return None


def download_mp4(url, output_path, playlist_items=None, create_subfolder=True, cookies_browser=None):
    """Скачивает видео в формате MP4"""
    # Определяем шаблон пути в зависимости от того, плейлист это или нет
    is_playlist, playlist_name, count = check_if_playlist(url)
    
    if is_playlist and create_subfolder:
        # Для плейлиста создаем подпапку
        outtmpl = os.path.join(output_path, '%(playlist)s', '%(playlist_index)s - %(title)s.%(ext)s')
    else:
        outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'ignoreerrors': True,
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = cookies_browser
    
    if playlist_items:
        ydl_opts['playlist_items'] = playlist_items
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if is_playlist:
            print(f"📋 Обнаружен плейлист: {playlist_name}")
            print(f"📊 Количество видео: {count}")
        print(f"🎥 Скачиваю видео в MP4...")
        print()
        ydl.download([url])
        print("\n✅ Видео успешно скачано!")


def download_mp3(url, output_path, playlist_items=None, create_subfolder=True, cookies_browser=None):
    """Скачивает аудио в формате MP3"""
    is_playlist, playlist_name, count = check_if_playlist(url)
    
    if is_playlist and create_subfolder:
        outtmpl = os.path.join(output_path, '%(playlist)s', '%(playlist_index)s - %(title)s.%(ext)s')
    else:
        outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'progress_hooks': [progress_hook],
        'ignoreerrors': True,
        'no_warnings': False,
        'keepvideo': True,  # Сохраняем оригинальное видео после конвертации в MP3
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = cookies_browser
    
    if playlist_items:
        ydl_opts['playlist_items'] = playlist_items
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if is_playlist:
            print(f"📋 Обнаружен плейлист: {playlist_name}")
            print(f"📊 Количество видео: {count}")
        print(f"🎵 Скачиваю аудио в MP3...")
        print()
        ydl.download([url])
        print("\n✅ Аудио успешно скачано!")


def progress_hook(d):
    """Отображает прогресс скачивания"""
    if d['status'] == 'downloading':
        try:
            percent = d.get('_percent_str', '???')
            speed = d.get('_speed_str', '???')
            eta = d.get('_eta_str', '???')
            filename = d.get('filename', '').split('/')[-1]
            print(f"\r⏬ {filename[:50]:<50} | {percent:>7} | {speed:>12} | ETA: {eta:>8}", end='', flush=True)
        except Exception:
            pass
    elif d['status'] == 'finished':
        filename = d.get('filename', '').split('/')[-1]
        print(f"\r✓ {filename[:50]:<50} | Завершено!{' '*30}")
    elif d['status'] == 'error':
        print(f"\r❌ Ошибка при скачивании{' '*70}")


def main():
    parser = argparse.ArgumentParser(
        description='Скачивание видео с YouTube в форматах MP4 и MP3. Поддерживает отдельные видео и плейлисты.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  Одно видео:
    %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID" --format mp4
    %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID" --format mp3
    %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID" --format both
  
  Весь плейлист:
    %(prog)s "https://www.youtube.com/playlist?list=PLAYLIST_ID" --format mp4
    %(prog)s "https://www.youtube.com/playlist?list=PLAYLIST_ID" --format mp3
  
  Определенные видео из плейлиста:
    %(prog)s "https://www.youtube.com/playlist?list=PLAYLIST_ID" --items "1-5"
    %(prog)s "https://www.youtube.com/playlist?list=PLAYLIST_ID" --items "1,3,5,7"
    %(prog)s "https://www.youtube.com/playlist?list=PLAYLIST_ID" --items "10-20,25,30-35"
  
  С указанием папки:
    %(prog)s "URL" --format mp4 --output ~/Videos
  
  Без создания подпапки для плейлиста:
    %(prog)s "PLAYLIST_URL" --no-subfolder
        """
    )
    
    parser.add_argument('url', help='URL видео или плейлиста YouTube')
    parser.add_argument(
        '--format', '-f',
        choices=['mp4', 'mp3', 'both'],
        default='mp4',
        help='Формат для скачивания (по умолчанию: mp4)'
    )
    parser.add_argument(
        '--output', '-o',
        default=os.path.expanduser('~/Downloads'),
        help='Папка для сохранения файлов (по умолчанию: ~/Downloads)'
    )
    parser.add_argument(
        '--items', '-i',
        default=None,
        help='Номера видео для скачивания из плейлиста (например: "1-5", "1,3,5", "10-20,25")'
    )
    parser.add_argument(
        '--no-subfolder',
        action='store_true',
        help='Не создавать подпапку для плейлиста'
    )
    
    args = parser.parse_args()
    
    # Создаём папку если её нет
    output_path = Path(args.output).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)
    
    create_subfolder = not args.no_subfolder
    
    print("=" * 80)
    print("🎬 YouTube Downloader")
    print("=" * 80)
    print(f"📁 Папка для сохранения: {output_path}")
    print(f"🔗 URL: {args.url}")
    print(f"📦 Формат: {args.format.upper()}")
    if args.items:
        print(f"🔢 Выбранные видео: {args.items}")
    print("=" * 80)
    print()
    
    # Пробуем получить cookies из браузера
    cookies_browser = try_get_cookies()
    print()
    
    try:
        if args.format == 'mp4':
            download_mp4(args.url, str(output_path), args.items, create_subfolder, cookies_browser)
        elif args.format == 'mp3':
            download_mp3(args.url, str(output_path), args.items, create_subfolder, cookies_browser)
        elif args.format == 'both':
            download_mp4(args.url, str(output_path), args.items, create_subfolder, cookies_browser)
            print()
            print("=" * 80)
            print()
            download_mp3(args.url, str(output_path), args.items, create_subfolder, cookies_browser)
        
        print()
        print("=" * 80)
        print("🎉 Все файлы успешно скачаны!")
        print("=" * 80)
    except KeyboardInterrupt:
        print("\n\n⚠️  Скачивание прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Ошибка при скачивании: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
