
import argparse
import os
import struct
import wave
from datetime import datetime
from threading import Thread

import pvporcupine
from pvrecorder import PvRecorder

import argparse
from threading import Thread

from pvcheetah import *

class WakeWordDemo(Thread):
    def __init__(
            self,
            access_key: str,
            library_path: str,
            model_path: str,
            keyword_paths: list,
            sensitivities: list,
            input_device_index: Optional[int] = None,
            endpoint_duration_sec: float = 0.5,
            enable_automatic_punctuation: bool = False):
        super(WakeWordDemo, self).__init__()

        self._access_key = access_key
        self._library_path = library_path
        self._model_path = model_path
        self._keyword_paths = keyword_paths
        self._sensitivities = sensitivities
        self._input_device_index = input_device_index
        self._endpoint_duration_sec = endpoint_duration_sec
        self._enable_automatic_punctuation = enable_automatic_punctuation
        self._is_recording = False
        self._stop = False

    def run(self):
        self._is_recording = True

        keywords = list()
        for x in self._keyword_paths:
            keyword_phrase_part = os.path.basename(x).replace('.ppn', '').split('_')
            if len(keyword_phrase_part) > 6:
                keywords.append(' '.join(keyword_phrase_part[0:-6]))
            else:
                keywords.append(keyword_phrase_part[0])

        o = None
        porcupine = None
        recorder = None

        try:
            porcupine = pvporcupine.create(
                access_key=self._access_key,
                library_path=self._library_path,
                model_path=self._model_path,
                keyword_paths=self._keyword_paths,
                sensitivities=self._sensitivities)

            recorder = PvRecorder(device_index=self._input_device_index, frame_length=porcupine.frame_length)
            recorder.start()

            while True:
                pcm = recorder.read()
                if porcupine.process(pcm) == 0:
                    print("Wake word detected!")
                    o = create(
                        access_key=self._access_key,
                        library_path=self._library_path,
                        model_path=self._model_path,
                        endpoint_duration_sec=self._endpoint_duration_sec)
                    print('Cheetah version : %s' % o.version)
                    while True:
                        partial_transcript, is_endpoint = o.process(recorder.read())
                        print(partial_transcript, end='', flush=True)
                        if is_endpoint:
                            print(o.flush())
                            o.delete()
                            break
                elif self._stop:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            if recorder is not None:
                recorder.stop()

            if porcupine is not None:
                porcupine.delete()
            if o is not None:
                o.delete()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--access_key',
                        help='AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)')

    parser.add_argument(
        '--keywords',
        nargs='+',
        help='List of default keywords for detection. Available keywords: %s' % ', '.join(sorted(pvporcupine.KEYWORDS)),
        choices=sorted(pvporcupine.KEYWORDS),
        metavar='')

    parser.add_argument(
        '--keyword_paths',
        nargs='+',
        help="Absolute paths to keyword model files. If not set it will be populated from `--keywords` argument")

    parser.add_argument('--library_path', help='Absolute path to dynamic library.', default=pvporcupine.LIBRARY_PATH)

    parser.add_argument(
        '--model_path',
        help='Absolute path to the file containing model parameters.',
        default=pvporcupine.MODEL_PATH)

    parser.add_argument(
        '--sensitivities',
        nargs='+',
        help="Sensitivities for detecting keywords. Each value should be a number within [0, 1]. A higher "
             "sensitivity results in fewer misses at the cost of increasing the false alarm rate. If not set 0.5 "
             "will be used.",
        type=float,
        default=None)

    parser.add_argument('--audio_device_index', help='Index of input audio device.', type=int, default=-1)

    parser.add_argument('--output_path', help='Absolute path to recorded audio for debugging.', default=None)

    parser.add_argument('--show_audio_devices', action='store_true')

    parser.add_argument('--endpoint_duration_sec', type=float, default=1.)

    parser.add_argument('--disable_automatic_punctuation', action='store_true')

    args = parser.parse_args()

    if args.show_audio_devices:
        PorcupineDemo.show_audio_devices()
    else:
        if args.access_key is None:
            raise ValueError("AccessKey (--access_key) is required")
        if args.keyword_paths is None:
            if args.keywords is None:
                raise ValueError("Either `--keywords` or `--keyword_paths` must be set.")

            keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in args.keywords]
        else:
            keyword_paths = args.keyword_paths

        if args.sensitivities is None:
            args.sensitivities = [0.5] * len(keyword_paths)

        if len(keyword_paths) != len(args.sensitivities):
            raise ValueError('Number of keywords does not match the number of sensitivities.')

        WakeWordDemo(
            keyword_paths=args.keyword_paths,
            sensitivities=args.sensitivities,
            access_key=args.access_key,
            library_path=args.library_path,
            model_path=args.model_path,
            input_device_index=args.audio_device_index,
            endpoint_duration_sec=args.endpoint_duration_sec,
            enable_automatic_punctuation=not args.disable_automatic_punctuation).run()


if __name__ == '__main__':
    main()