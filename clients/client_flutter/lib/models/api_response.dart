class ApiResponse {
  final String message;
  final bool success;
  final int? statusCode;

  ApiResponse({required this.message, required this.success, this.statusCode});

  factory ApiResponse.fromJson(Map<String, dynamic> json, int statusCode) {
    return ApiResponse(
      message: json['message'] ?? '',
      success: statusCode >= 200 && statusCode < 300,
      statusCode: statusCode,
    );
  }
}
