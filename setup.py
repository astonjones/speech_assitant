import os
import shutil

import setuptools

os.system('git clean -dfx')

package_folder = os.path.join(os.path.dirname(__file__), 'speech_assistant')
os.mkdir(package_folder)

shutil.copy(
    os.path.join(os.path.dirname(__file__), 'speech_assistant_mic.py'),
    os.path.join(package_folder, 'speech_assistant_mic.py'))

with open(os.path.join(os.path.dirname(__file__), 'MANIFEST.in'), 'w') as f:
#     f.write('include speech_assistant/speech_assistant_file.py\n')
    f.write('include speech_assistant/speech_assistant_mic.py\n')

with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as f:
    long_description = f.read()

setuptools.setup(
    name="speech_assistant",
    version="2.1.6",
    author="Aston Jones",
    author_email="aston@divinationhomes.com",
    description="This app is going to be a speech assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/astonjones/speech_assitant",
    packages=["speech_assistant"],
    install_requires=["pvporcupine==2.1.4", "pvrecorder==1.1.1"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Sound/Audio :: Speech"
    ],
    entry_points=dict(
        console_scripts=[
            'speech_assistant_mic=speech_assistant.speech_assistant_mic:main',
        ],
    ),
    python_requires='>=3.5',
    keywords="Speech",
)