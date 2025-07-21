import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'viewmodels/sensor_viewmodel.dart';
import 'viewmodels/actuator_viewmodel.dart';
import 'views/home_view.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (context) => SensorViewModel()),
        ChangeNotifierProvider(create: (context) => ActuatorViewModel()),
      ],
      child: MaterialApp(
        title: 'Cidade Inteligente',
        theme: ThemeData(
          colorScheme:
              ColorScheme.fromSeed(
                seedColor: const Color(0xFF6B73FF),
                brightness: Brightness.light,
              ).copyWith(
                primary: const Color(0xFF6B73FF),
                secondary: const Color(0xFF9C27B0),
                surface: const Color(0xFFF8F9FA),
                background: const Color(0xFFF1F3F4),
              ),
          useMaterial3: true,
          cardTheme: const CardThemeData(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(16)),
            ),
            color: Colors.white,
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Color(0xFF6B73FF), width: 2),
            ),
            filled: true,
            fillColor: Colors.grey.shade50,
          ),
        ),
        home: const HomeView(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
