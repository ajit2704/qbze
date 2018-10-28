/*
 * Copyright 2017-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except
 * in compliance with the License. A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0/
 *
 * or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 */
package com.example.root.smartbaniya;

import android.app.Activity;
import android.content.Context;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import com.amazonaws.mobileconnectors.dynamodbv2.document.datatype.Document;
import android.support.design.widget.TextInputLayout;
import android.support.v7.widget.Toolbar;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.WindowManager;
import android.content.SharedPreferences;
import android.widget.Toast;
/**
 * Activity that displays the Edit Memo Screen
 */
public class EditActivity extends Activity {
    /**
     * The Text Editor
     */
    SharedPreferences sharedpreferences;
    private EditText metText,meditText,meditText1,meditText2;
    private TextInputLayout inputLayoutName, inputLayoutEmail, inputLayoutMobile, inputLayoutAddress;
    /**
     * The Memo being edited
     */
    private Document memo;

    public static final String mypreference = "mypref";
    public static final String Name = "nameKey";
    public static final String Email = "emailKey";
    public static final String Mobile = "mobileKey";
    public static final  String Address = "addressKey";

    /**
     * Lifecycle method called when the activity is created
     * @param savedInstanceState the bundle
     */
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_edit);


        // Bind the view variables
        metText = findViewById(R.id.input_name);
        meditText = findViewById(R.id.input_email);
        meditText1 = findViewById(R.id.input_mobile);
        meditText2 = findViewById(R.id.input_address);
        inputLayoutName = (TextInputLayout) findViewById(R.id.input_layout_name);
        inputLayoutEmail = (TextInputLayout) findViewById(R.id.input_layout_email);
        inputLayoutMobile = (TextInputLayout) findViewById(R.id.input_layout_mobile);
        inputLayoutAddress = (TextInputLayout) findViewById(R.id.input_layout_address);
        metText.addTextChangedListener(new MyTextWatcher(metText));
        meditText.addTextChangedListener(new MyTextWatcher(meditText));
        meditText1.addTextChangedListener(new MyTextWatcher(meditText1));
        meditText2.addTextChangedListener(new MyTextWatcher(meditText2));
        // If this activity was passed an intent, then receive the noteId of
        // the memo to edit and populate the UI with the content
        sharedpreferences = getSharedPreferences(mypreference,
                Context.MODE_PRIVATE);
        if (sharedpreferences.contains(Name)) {
            metText.setText(sharedpreferences.getString(Name, ""));
        }
        if (sharedpreferences.contains(Email)) {
            meditText.setText(sharedpreferences.getString(Email, ""));

        }
        if (sharedpreferences.contains(Mobile)) {
            meditText1.setText(sharedpreferences.getString(Mobile, ""));
        }
        if (sharedpreferences.contains(Address)) {
            meditText2.setText(sharedpreferences.getString(Address, ""));

        }

        Bundle bundle = getIntent().getExtras();
        if (bundle != null) {
            GetItemAsyncTask task = new GetItemAsyncTask();
            task.execute((String) bundle.get("MEMO"));
        }
    }

    /**
     * Event Handler called when the Save button is clicked
     * @param view the initiating view
     */
    public void onSaveClicked(View view) {
        if (memo == null) {

            Document newMemo = new Document();
            newMemo.put("userId", meditText.getText().toString());
            newMemo.put("name", metText.getText().toString());
            newMemo.put("email", meditText.getText().toString());
            newMemo.put("mobile_no", meditText1.getText().toString());
            newMemo.put("Address", meditText2.getText().toString());
            CreateItemAsyncTask task = new CreateItemAsyncTask();
            task.execute(newMemo);
        } else {
            memo.put("userId", meditText.getText().toString());

            memo.put("name", metText.getText().toString());
            memo.put("email", meditText.getText().toString());
            UpdateItemAsyncTask task = new UpdateItemAsyncTask();
            task.execute(memo);
        }
        // Finish this activity and return to the prior activity
        SharedPreferences.Editor editor = sharedpreferences.edit();
        editor.putString(Name, metText.getText().toString());
        editor.putString(Email, meditText.getText().toString());
        editor.putString(Mobile, meditText1.getText().toString());
        editor.putString(Address, meditText2.getText().toString());
        editor.commit();
        this.finish();
    }

    /**
     * Event Handler called when the Cancel button is clicked
     * @param view the initiating view
     */
    public void onCancelClicked(View view) {
        this.finish();
    }

    /**
     * Async Task to retrieve a Memo by its noteId from the DynamoDB table
     */
    private class GetItemAsyncTask extends AsyncTask<String, Void, Document> {
        @Override
        protected Document doInBackground(String... documents) {
            DatabaseAccess databaseAccess = DatabaseAccess.getInstance(EditActivity.this);
            return databaseAccess.getMemoById(documents[0]);
        }

        @Override
        protected void onPostExecute(Document result) {
            if (result != null) {
                memo = result;
                metText.setText(memo.get("email").asString());
                meditText.setText(memo.get("mobile_no").asString());
            }
        }
    }

    /**
     * Async Task to create a new memo into the DynamoDB table
     */
    private class CreateItemAsyncTask extends AsyncTask<Document, Void, Void> {
        @Override
        protected Void doInBackground(Document... documents) {
            DatabaseAccess databaseAccess = DatabaseAccess.getInstance(EditActivity.this);
            databaseAccess.create(documents[0]);
            return null;
        }
    }

    /**
     * Async Task to save an existing memo into the DynamoDB table
     */
    private class UpdateItemAsyncTask extends AsyncTask<Document, Void, Void> {
        @Override
        protected Void doInBackground(Document... documents) {
            DatabaseAccess databaseAccess = DatabaseAccess.getInstance(EditActivity.this);
            databaseAccess.update(documents[0]);
            return null;
        }
    }

    private boolean validateName() {
        if (metText.getText().toString().trim().isEmpty()) {
            inputLayoutName.setError(getString(R.string.err_msg_name));
            requestFocus(metText);
            return false;
        } else {
            inputLayoutName.setErrorEnabled(false);
        }

        return true;
    }

    private boolean validateEmail() {
        String email = meditText.getText().toString().trim();

        if (email.isEmpty() || !isValidEmail(email)) {
            inputLayoutEmail.setError(getString(R.string.err_msg_email));
            requestFocus(meditText);
            return false;
        } else {
            inputLayoutEmail.setErrorEnabled(false);
        }

        return true;
    }

    private boolean validateMobile() {
        if (meditText1.getText().toString().trim().isEmpty()) {
            inputLayoutMobile.setError(getString(R.string.err_msg_mobile));
            requestFocus(meditText1);
            return false;
        } else {
            inputLayoutMobile.setErrorEnabled(false);
        }

        return true;
    }
    private  boolean validateAddress(){
        if (meditText2.getText().toString().trim().isEmpty()) {
            inputLayoutAddress.setError(getString(R.string.err_msg_address));
        }else {
            inputLayoutAddress.setErrorEnabled(false);
        }

        return true;
    }

    private static boolean isValidEmail(String email) {
        return !TextUtils.isEmpty(email) && android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches();
    }

    private void requestFocus(View view) {
        if (view.requestFocus()) {
            getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
        }
    }
    private class MyTextWatcher implements TextWatcher {

        private View view;

        private MyTextWatcher(View view) {
            this.view = view;
        }

        public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {
        }

        public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {
        }

        public void afterTextChanged(Editable editable) {
            switch (view.getId()) {
                case R.id.input_name:
                    validateName();
                    break;
                case R.id.input_email:
                    validateEmail();
                    break;
                case R.id.input_mobile:
                    validateMobile();
                    break;
                case R.id.input_address:
                    validateAddress();
                    break;

            }
        }
    }
}
