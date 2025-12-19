#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys

def setup_logger(name: str = "", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a consistent logger for the entire project.

    - Configures the root logger once (first import).
    - Subsequent calls reuse the same configuration.
    - Prevents duplicate handlers.
    - Each module can call this safely: logger = setup_logger(__name__)

    Args:
        name: The name for the logger (usually __name__).
        level: Logging level (default: INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Configure the root logger only once
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)

    # Ensure all child loggers propagate to the root
    logger.propagate = True
    return logger

