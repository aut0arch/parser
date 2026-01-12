
package com.example;

public class UserManager {
    public void createUser(String name) {
        System.out.println("Creating user " + name);
        Helper.validate(name);
    }
}
