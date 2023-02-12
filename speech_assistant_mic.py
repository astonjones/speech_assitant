
import argparse
import os
import struct
from typing import Optional
import wave
import openai
from datetime import datetime
from threading import Thread

import pvporcupine
from pvrecorder import PvRecorder

import argparse
from threading import Thread

import pvcheetah
from google.cloud import texttospeech
from playsound import playsound

class TextToSpeech(Thread):
    def __init__(
            self,
            passed_text):
        super(TextToSpeech, self).__init__()
        self.__passed_text = passed_text

    def run(self):
        try:
            print("call to google text to speach initiated")
            # Instantiates a client
            client = texttospeech.TextToSpeechClient()

            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text="Popcorn in my mouth!")

            # Build the voice request, select the language code ("en-US") and the ssml
            # voice gender ("neutral")
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )

            # CHANGE THIS TO NOT ACCEPT A FILE BUT A STRING??
            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            # Perform the text-to-speech request on the text input with the selected
            # voice parameters and audio file type
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            mp3FilePath = "outputFile.mp3"

            # The response's audio_content is binary.
            with open(mp3FilePath, "wb") as out:
                # Write the response to the output file.
                out.write(response.audio_content)
            print('Audio content written to file "output.mp3"')
        finally:
            print("Call to t2s ended")
            playsound(mp3FilePath)



class CallToChatGPT(Thread):
    def __init__(
            self,
            passed_prompt):
        super(CallToChatGPT, self).__init__()
        self._passed_prompt = passed_prompt


    def run(self):
        try:
            print("prompt = %s " % self._passed_prompt)
            response = openai.Completion.create(engine="text-curie-001", prompt=self._passed_prompt)
            print(response["choices"][0]["text"])
        finally:
            print("end of call to chatgpt")



class CheetahDemo(Thread):
    def __init__(
            self,
            passed_recorder,
            access_key: str,
            model_path: Optional[str],
            library_path: Optional[str],
            endpoint_duration_sec: float,
            enable_automatic_punctuation: bool):
        super(CheetahDemo, self).__init__()

        self._passed_recorder = passed_recorder
        self._access_key = access_key
        self._model_path = model_path
        self._library_path = library_path
        self._endpoint_duration_sec = endpoint_duration_sec
        self._enable_automatic_punctuation = enable_automatic_punctuation
        self._is_recording = False
        self._stop = False

    def run(self):
        self._is_recording = True
        recorder = self._passed_recorder

        cheetah = None
        fullTranscript = ''

        try:
            cheetah = pvcheetah.create(
                access_key=self._access_key,
                library_path=self._library_path,
                model_path=self._model_path,
                endpoint_duration_sec=5)
            recorder.start()

            print('Cheetah version : %s' % cheetah.version)

            while True:
                fullTranscript += cheetah.process(recorder.read())[0]
                is_endpoint = cheetah.process(recorder.read())[1]
                if is_endpoint:
                    recorder.stop()
                    fullTranscript += cheetah.flush()
                    print('fullest transcript %s ' % fullTranscript)
                    gpt_call = CallToChatGPT(fullTranscript)
                    gpt_call.run()
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            recorder.stop()

            if cheetah is not None:
                cheetah.delete()


class PorcupineDemo(Thread):

    def __init__(
            self,
            access_key,
            library_path,
            model_path,
            keyword_paths,
            sensitivities,
            endpoint_duration_sec,
            enable_automatic_punctuation,
            input_device_index=None,
            output_path=None):

        super(PorcupineDemo, self).__init__()

        self._access_key = access_key
        self._library_path = library_path
        self._model_path = model_path
        self._keyword_paths = keyword_paths
        self._sensitivities = sensitivities
        self._input_device_index = input_device_index
        self._endpoint_duration_sec = endpoint_duration_sec
        self._enable_automatic_punctuation = enable_automatic_punctuation
        self._output_path = output_path

    def run(self):
        openai.api_key = os.getenv("OPENAI_ACCESS_KEY")
        keywords = list()
        # GO through this for loop and see if it neccessary
        for x in self._keyword_paths:
            keyword_phrase_part = os.path.basename(x).replace('.ppn', '').split('_')
            if len(keyword_phrase_part) > 6:
                keywords.append(' '.join(keyword_phrase_part[0:-6]))
            else:
                keywords.append(keyword_phrase_part[0])

        porcupine = None
        recorder = None
        wav_file = None
        try:
            porcupine = pvporcupine.create(
                access_key=self._access_key,
                library_path=self._library_path,
                model_path=self._model_path,
                keyword_paths=self._keyword_paths,
                sensitivities=self._sensitivities)

            recorder = PvRecorder(device_index=self._input_device_index, frame_length=porcupine.frame_length)

            if self._output_path is not None:
                wav_file = wave.open(self._output_path, "w")
                wav_file.setparams((1, 2, 16000, 512, "NONE", "NONE"))

            print('Using device: %s', recorder.selected_device)

            print('Listening {')
            for keyword, sensitivity in zip(keywords, self._sensitivities):
                print('  %s (%.2f)' % (keyword, sensitivity))
            print('}')

            while True:
                recorder.start()
                pcm = recorder.read()

                if wav_file is not None:
                    wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

                result = porcupine.process(pcm)
                if result >= 0:
                    recorder.stop()
                    # Right here i need to give the logic to turn speech into text
                    print('[%s] Detected %s' % (str(datetime.now()), keywords[result]))
                    demo = CheetahDemo(access_key=self._access_key,
                                passed_recorder=recorder,
                                model_path=None,
                                library_path=None,
                                endpoint_duration_sec=0.5,
                                enable_automatic_punctuation=True)
                    demo.run()

        except pvporcupine.PorcupineInvalidArgumentError as e:
            args = (
                self._access_key,
                self._library_path,
                self._model_path,
                self._keyword_paths,
                self._sensitivities,
            )
            print("One or more arguments provided to Porcupine is invalid: ", args)
            print("If all other arguments seem valid, ensure that '%s' is a valid AccessKey" % self._access_key)
            raise e
        except pvporcupine.PorcupineActivationError as e:
            print("AccessKey activation error")
            raise e
        except pvporcupine.PorcupineActivationLimitError as e:
            print("AccessKey '%s' has reached it's temporary device limit" % self._access_key)
            raise e
        except pvporcupine.PorcupineActivationRefusedError as e:
            print("AccessKey '%s' refused" % self._access_key)
            raise e
        except pvporcupine.PorcupineActivationThrottledError as e:
            print("AccessKey '%s' has been throttled" % self._access_key)
            raise e
        except pvporcupine.PorcupineError as e:
            print("Failed to initialize Porcupine")
            raise e
        except KeyboardInterrupt:
            print('Stopping ...')
        finally:
            if porcupine is not None:
                porcupine.delete()

            if recorder is not None:
                recorder.delete()

            if wav_file is not None:
                wav_file.close()

    @classmethod
    def show_audio_devices(cls):
        devices = PvRecorder.get_audio_devices()

        for i in range(len(devices)):
            print('index: %d, device name: %s' % (i, devices[i]))


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

        # PorcupineDemo(
        #     access_key=args.access_key,
        #     library_path=args.library_path,
        #     model_path=args.model_path,
        #     keyword_paths=keyword_paths,
        #     sensitivities=args.sensitivities,
        #     output_path=args.output_path,
        #     input_device_index=args.audio_device_index,
        #     endpoint_duration_sec=args.endpoint_duration_sec,
        #     enable_automatic_punctuation=not args.disable_automatic_punctuation).run()

        TextToSpeech(passed_text='Text to be said').run()


if __name__ == '__main__':
    main()