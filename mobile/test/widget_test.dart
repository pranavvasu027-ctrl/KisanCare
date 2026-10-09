import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/main.dart';
import 'package:mobile/features/home/home_screen.dart';


void main() {
  testWidgets('App loads smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const KisanCareApp());
    expect(find.byType(HomeScreen), findsOneWidget);
  });
}
