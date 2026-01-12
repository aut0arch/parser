
package com.example;

public class Helper {
    public static void validate(String input) {
        if (input == null) throw new RuntimeException("Invalid");
    }
}
