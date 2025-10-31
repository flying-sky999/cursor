"""
????????
"""
import subprocess
import os

def create_test_video():
    """?? ffmpeg ??????????? ffmpeg ???????"""
    
    output_path = "test_files/test_video.mp4"
    os.makedirs("test_files", exist_ok=True)
    
    # ??1: ???? ffmpeg ??
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode == 0:
            print("?? ffmpeg?????????...")
            cmd = [
                'ffmpeg', '-f', 'lavfi', 
                '-i', 'testsrc=duration=3:size=1280x720:rate=30',
                '-pix_fmt', 'yuv420p',
                '-c:v', 'libx264',
                output_path, '-y'
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"???????: {output_path}")
            return output_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ffmpeg ???")
    
    # ??2: ??????? MP4 ??
    print("??????????...")
    # ????????? MP4 ????1??????
    minimal_mp4 = bytes([
        0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70, 0x69, 0x73, 0x6f, 0x6d,
        0x00, 0x00, 0x02, 0x00, 0x69, 0x73, 0x6f, 0x6d, 0x69, 0x73, 0x6f, 0x32,
        0x61, 0x76, 0x63, 0x31, 0x6d, 0x70, 0x34, 0x31
    ])
    
    # ???????????
    with open(output_path, 'wb') as f:
        # ????? MP4 ??
        f.write(minimal_mp4)
        # ???????????
        f.write(b'\x00' * 1024)
    
    print(f"???????????: {output_path}")
    return output_path

if __name__ == "__main__":
    create_test_video()
