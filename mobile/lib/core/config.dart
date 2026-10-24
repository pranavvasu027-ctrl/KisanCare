import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class EnvironmentConfig {
  /// Timeout for API requests
  static const Duration apiTimeout = Duration(seconds: 15);

  /// Change this to test on a physical device.
  /// Example: '192.168.1.100'
  static const String _devHostAddress = '127.0.0.1';

  /// Port where FastAPI is running
  static const String _apiPort = '8000';

  /// Base URL for the FastAPI backend.
  static String get apiBaseUrl {
    if (kIsWeb) {
      return 'http://$_devHostAddress:$_apiPort';
    }

    try {
      if (Platform.isAndroid) {
        // Use 10.0.2.2 for Android emulators, unless testing physical device where devHostAddress should be used.
        // If testing on a physical device, change _devHostAddress and return it here instead.
        return 'http://10.0.2.2:$_apiPort';
      }
    } catch (e) {
      // Fallback if platform fails
    }

    return 'http://$_devHostAddress:$_apiPort';
  }
}
