import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';

class ApiException implements Exception {
  final String message;
  final int statusCode;

  ApiException(this.message, this.statusCode);

  @override
  String toString() => 'ApiException: $message (Status: $statusCode)';
}

class ApiClient {
  static final http.Client _client = http.Client();

  /// Retrieve headers. Attach Auth token here when authentication is implemented.
  static Map<String, String> _getHeaders() {
    return {
      'Content-Type': 'application/json',
      // 'Authorization': 'Bearer \$token', // TODO: Add token when auth is implemented
    };
  }

  static Future<dynamic> get(String endpoint) async {
    final uri = Uri.parse('\${EnvironmentConfig.apiBaseUrl}$endpoint');

    try {
      final response = await _client
          .get(uri, headers: _getHeaders())
          .timeout(EnvironmentConfig.apiTimeout);

      return _processResponse(response);
    } catch (e) {
      _handleNetworkError(e);
    }
  }

  static Future<dynamic> post(String endpoint, {Map<String, dynamic>? body}) async {
    final uri = Uri.parse('\${EnvironmentConfig.apiBaseUrl}$endpoint');

    try {
      final response = await _client
          .post(uri, headers: _getHeaders(), body: body != null ? jsonEncode(body) : null)
          .timeout(EnvironmentConfig.apiTimeout);

      return _processResponse(response);
    } catch (e) {
      _handleNetworkError(e);
    }
  }

  static dynamic _processResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      return jsonDecode(response.body);
    } else {
      String errorMessage = 'Server error';
      try {
        final decoded = jsonDecode(response.body);
        if (decoded is Map && decoded.containsKey('detail')) {
          errorMessage = decoded['detail'].toString();
        }
      } catch (_) {
        // Body is not json
        errorMessage = response.body.isNotEmpty ? response.body : response.reasonPhrase ?? 'Unknown error';
      }
      throw ApiException(errorMessage, response.statusCode);
    }
  }

  static void _handleNetworkError(dynamic error) {
    if (error is ApiException) {
      throw error; // Re-throw api exceptions
    }
    // Handle timeouts or socket exceptions
    throw ApiException('Network error or timeout occurred: \$error', 0);
  }
}
