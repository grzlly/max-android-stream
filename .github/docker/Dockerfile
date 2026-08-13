FROM ubuntu:22.04

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install core dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    libpulse0 \
    libgl1 \
    fluxbox \
    aapt \
    x11-utils \
    x11-xserver-utils \
    scrcpy \
    nodejs \
    npm \
    curl \
    wget \
    unzip \
    git \
    openjdk-17-jre-headless \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Setup Android SDK environment variables
ENV ANDROID_HOME=/opt/android-sdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV ANDROID_AVD_HOME=/root/.android/avd
ENV PATH=${PATH}:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${ANDROID_HOME}/emulator

# Download and install Android Command Line Tools
RUN mkdir -p ${ANDROID_HOME}/cmdline-tools && \
    cd ${ANDROID_HOME}/cmdline-tools && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O cmdline-tools.zip && \
    unzip -q cmdline-tools.zip && \
    rm cmdline-tools.zip && \
    mv cmdline-tools latest

# Accept licenses and install Android SDK components
RUN yes | sdkmanager --licenses && \
    sdkmanager "platform-tools" "platforms;android-30" "system-images;android-30;google_apis;x86_64" "emulator"

# Create AVD max_device
RUN echo "no" | avdmanager create avd -n max_device -k "system-images;android-30;google_apis;x86_64" --device "pixel"

# Workaround for emulator in Docker (software rendering compatibility)
RUN mkdir -p /root/.android && echo "hw.gpu.mode=swiftshader_indirect" >> /root/.android/avd/max_device.avd/config.ini

# Ensure emulator has executable permissions
RUN chmod +x ${ANDROID_HOME}/emulator/emulator

# Default command
CMD ["/bin/bash"]
