function makeEmergencyCall(functionArgs) {
    const { emergencyPrompt } = functionArgs;
    console.log("GPT -> called makeEmergencyCall function");
    
    // Simulate the decision process and call attempt
    let status = "success";
    let message = "";
  
    if (emergencyPrompt === "medical" || emergencyPrompt === "ambulance" || emergencyPrompt === "hospital") {
      message = `Emergency services alerted, calling local hospital.`;
    } else {
      status = "failure";
    }
    
    return JSON.stringify({ status, message });
  }
  
  module.exports = makeEmergencyCall;