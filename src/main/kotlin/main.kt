import com.google.auth.oauth2.GoogleCredentials
import com.google.cloud.firestore.Firestore
import com.google.cloud.firestore.FirestoreOptions
import com.sphericalchickens.osmptrailchallenge.loaders.GpsLoaderFactory
import java.nio.file.Path
import java.nio.file.Paths


//////////////////// Note //////////////////////////////
//
// For debugging add to the VM args in the launcher
// -Dorg.slf4j.simpleLogger.defaultLogLevel=trace
//
//////////////////// Note //////////////////////////////

fun main(args: Array<String>) {
  // Strava athleteId.  Set this to your own Strava ID (or test account).
  val stravaAthleteId = "929553"
  // Username of the user being processed.  Set this to your own account id (or test account).
  val athleteId = "dkhawk@gmail.com"

  // Example activities to load.
  // The gpx file is from Strava and the stravaId here is the strava activity id.
  // It is available in the activity url.
  val southBoulderCreekLoop = TestActivity(
    stravaActivityId = "4539099599",
    filename = "/Users/dkhawk/Downloads/Twilight_Amblers.gpx"
  )
  val wonderLandToEagle = TestActivity(
    stravaActivityId = "4566776467",
    filename = "/Users/dkhawk/Downloads/Wonderland_to_Eagle.gpx"
  )
  val activity = wonderLandToEagle

  // Everything below this should just work.  But it is possible the current directory isn't as
  // expected.
  // =====================================

  val dataDirectory: Path = Paths.get(System.getProperty("user.dir"), "src/main/resources")
  val trailDataFileName = Paths.get(dataDirectory.toString(), "OSMP_Trails.kml").toString()
  val trailTextFilename = Paths.get(dataDirectory.toString(),"OSMP-trails.txt").toString()
  val gridTextFilename = Paths.get(dataDirectory.toString(),"grid.txt").toString()

  val database = getFirestoreConnection()

  val controller =
    initializeController(trailTextFilename, gridTextFilename, trailDataFileName, database)

  processActivity(controller, activity.filename, activity.stravaActivityId,
                  athleteId = athleteId, stravaId = stravaAthleteId)
}

data class TestActivity(val stravaActivityId: String, val filename: String)

private fun processActivity(
  controller: TrailChallengeController,
  activityFile: String,
  activityId: String,
  athleteId: String,
  stravaId: String,
) {
  val activity = controller.loadActivity(activityFile, athleteId, activityId, stravaId)
  val completedSegments = controller.processActivity(activity).map { it.second }

  controller.updateSegmentsForAthlete(athleteId, activity, completedSegments)
}

private fun initializeController(
  trailTextFilename: String,
  gridTextFilename: String,
  trailDataFileName: String,
  database: Firestore
): TrailChallengeController {
  val loader = GpsLoaderFactory()
  val controller = TrailChallengeController(loader, database)
  controller.loadTrailsFromFile(trailTextFilename)
  controller.loadGridFromFile(gridTextFilename)

  val readFromFiles = true
  if (readFromFiles) {
    controller.loadTrailsFromFile(trailTextFilename)
    controller.loadGridFromFile(gridTextFilename)
  } else {
    controller.loadTrailsFromKml(trailDataFileName)
    controller.createGridFromTrails()
  }
  return controller
}

private fun Double.format(digits: Int): String = "%.${digits}f".format(this)

private fun getFirestoreConnection(): Firestore {
  val firestoreOptions = FirestoreOptions.getDefaultInstance().toBuilder()
    .setProjectId("boulder-trail-challenge")
    .setCredentials(GoogleCredentials.getApplicationDefault())
    .build()

  return firestoreOptions.service
}

private fun testDatabaseWrite() {
//  val docRef: DocumentReference = database.collection("users").document("alovelace")
//  // Add document data  with id "alovelace" using a hashmap
//  val data: MutableMap<String, Any> = HashMap()
//  data["first"] = "Ada"
//  data["last"] = "Lovelace"
//  data["born"] = 1815
//  //asynchronously write data
//  // val result: ApiFuture<WriteResult> = docRef.set(data)
//  val result = docRef.set(data)
//  // ...
//  // result.get() blocks on response
//  println("Update time : " + result.get().updateTime)
//
//  return
}
