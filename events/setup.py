from distutils.core import setup

classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Environment :: Win32 (MS Windows)',
  'Intended Audience :: Developers',
  'Intended Audience :: System Administrators',
  'License :: PSF',
  'Natural Language :: English',
  'Operating System :: Microsoft :: Windows :: Windows 95/98/2000',
  'Topic :: System :: Systems Administration'
]

setup (
  name = "events",
  version = "0.1",
  description = "Windows events",
  author = "Tim Golden",
  author_email = "tim.golden@iname.com",
  url = "http://tgolden.sc.sabren.com/python/events.html",
  license = "http://www.python.org/psf/license.html",
  py_modules = ["events"]
)

