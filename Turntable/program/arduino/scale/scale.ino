/* including libraries */
#include <HX711.h>
#include <LiquidCrystal_I2C.h>

/* digital pins definition */
HX711 hx(9, 10, 128, 0.002347418); // Clock, Data; Amplification Factor, coefficient
LiquidCrystal_I2C lcd(0x27, 16, 2); // Address, Number of columns, Number of rows

int weight = 0;

void setup() {
  Serial.begin(9600); // Used for debug
  hx.set_offset(-136670); // Offset to be at zero when nothing is on the scales 

  /* ***Initialisation du LCD*** */
  lcd.init(); // Initialize the lcd 
  lcd.clear(); // Clear the lcd screen  
  lcd.backlight(); // Set backlight on
  lcd.begin(16,2); // Start the LCD screen
  lcd.setCursor(3, 0); // Set the starting point
  lcd.print("Niryo 2019");
  delay(3000);
  lcd.clear();
}


void loop() {
  if(digitalRead(0) == LOW) { // If the button is pressed
    hx.tare(); // Tare the scales
  }

  /* Read ten values and make an average of these ten values */
  double sum1 = 0;
  for (int i = 0; i < 10; i++) {
    sum1 += hx.bias_read();
  }
  
  weight = Round(sum1/10); 
  Serial.println(weight);
  lcd.clear();
  lcd.setCursor(5, 1);
  lcd.print(sum1/10);
  lcd.print("g");
}

/* Used to round the value */
int Round(float float_number) {
  int number = int(float_number); // Cast float into an int
  if(float_number - number  >= 0.5) {
    number++; 
    return number; 
  }else {
    return number;
  }
}
