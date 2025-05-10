from setuptools import setup, find_packages

setup(
    name='smart_money_bot',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'python-dotenv',
        'pyyaml',
        'websockets',
        'requests',
        'numpy',
        'pandas',
        'fastapi',
        'uvicorn',
        'tradingview-ta',
        'python-telegram-bot==20.0'
    ],
    entry_points={
        'console_scripts': [
            'run-bot=bot.bot:main'
        ]
    },
    python_requires='>=3.8'
)